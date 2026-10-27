/* NestQuest — shared front-end helpers */

const API = {
  async request(url, options = {}) {
    const opts = { credentials: "same-origin", headers: {}, ...options };
    if (opts.body && !(opts.body instanceof FormData)) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(url, opts);
    let data = {};
    try { data = await res.json(); } catch (_) { /* empty body */ }
    if (!res.ok) {
      const err = new Error(data.detail || data.message || `Request failed (${res.status})`);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  },
  get(url) { return this.request(url); },
  post(url, body) { return this.request(url, { method: "POST", body }); },
  put(url, body) { return this.request(url, { method: "PUT", body }); },
  patch(url, body) { return this.request(url, { method: "PATCH", body }); },
  del(url) { return this.request(url, { method: "DELETE" }); },
};

function toast(message, type = "info") {
  const el = document.getElementById("toast");
  if (!el) return alert(message);
  el.textContent = message;
  el.className = `toast show ${type}`;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = "toast"; }, 3200);
}

function inr(n) {
  n = Math.round(Number(n) || 0);
  const s = n < 0 ? "-" : "";
  const d = String(Math.abs(n));
  if (d.length <= 3) return `${s}₹${d}`;
  const last3 = d.slice(-3);
  const rest = d.slice(0, -3);
  const groups = [];
  let r = rest;
  while (r.length > 2) { groups.unshift(r.slice(-2)); r = r.slice(0, -2); }
  if (r) groups.unshift(r);
  return `${s}₹${groups.join(",")},${last3}`;
}

function shortInr(n) {
  n = Math.abs(Number(n) || 0);
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)} L`;
  if (n >= 1e3) return `₹${Math.round(n / 1e3)}K`;
  return `₹${Math.round(n)}`;
}

function requireLogin(message = "Please log in to continue.") {
  toast(message, "error");
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  setTimeout(() => { window.location.href = `/login?next=${next}`; }, 700);
}

/* ---------- Dropdown menus ---------- */
document.addEventListener("click", (e) => {
  const toggle = e.target.closest("[data-menu-toggle]");
  const menu = document.querySelector("[data-menu]");
  if (toggle && menu) {
    menu.classList.toggle("open");
    e.stopPropagation();
    return;
  }
  if (menu && !e.target.closest("[data-menu]")) menu.classList.remove("open");
});

/* ---------- Logout ---------- */
document.addEventListener("click", async (e) => {
  if (!e.target.closest("[data-logout]")) return;
  try {
    await API.post("/api/auth/logout");
    toast("Logged out.", "success");
    setTimeout(() => { window.location.href = "/"; }, 500);
  } catch (err) { toast(err.message, "error"); }
});

/* ---------- Save / shortlist ---------- */
document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-save]");
  if (!btn) return;
  e.preventDefault();
  if (!window.NESTQUEST_AUTH) return requireLogin("Log in to shortlist properties.");
  const id = btn.dataset.save;
  btn.disabled = true;
  try {
    const res = await API.post(`/api/properties/${id}/save`);
    btn.classList.toggle("saved", res.saved);
    btn.querySelector("i")?.classList.toggle("bi-heart-fill", res.saved);
    btn.querySelector("i")?.classList.toggle("bi-heart", !res.saved);
    const label = btn.querySelector("span");
    if (label) label.textContent = res.saved ? "Shortlisted" : "Shortlist";
    toast(res.message, "success");
  } catch (err) {
    toast(err.message, "error");
  } finally {
    btn.disabled = false;
  }
});

/* ---------- Property form (post / edit) ---------- */
function initPropertyForm() {
  const form = document.getElementById("propertyForm");
  if (!form) return;

  const id = form.dataset.id || "";
  const isEdit = Boolean(id);
  const listingType = form.querySelector("[name=listing_type]");
  const propType = form.querySelector("[name=property_type]");

  /* ---- Image uploader (files are sent to Cloudinary only on save) ---- */
  const MAX_IMAGES = 15;
  const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
  // Each item: { url: string|null (already on Cloudinary), file: File|null (pending), preview: string }
  let items = (Array.isArray(window.NESTQUEST_IMAGES) ? window.NESTQUEST_IMAGES : [])
    .map(function (u) { return { url: u, file: null, preview: u }; });
  const uploader = document.getElementById("imageUploader");
  const imageInput = document.getElementById("imageInput");
  const previewGrid = document.getElementById("imagePreviews");

  function renderPreviews() {
    if (!previewGrid) return;
    previewGrid.innerHTML = "";
    items.forEach(function (it, idx) {
      const item = document.createElement("div");
      item.className = "upload-item";

      const img = document.createElement("img");
      img.src = it.preview;
      img.alt = "Property photo " + (idx + 1);

      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "upload-remove";
      removeBtn.dataset.removeImage = String(idx);
      const removeIcon = document.createElement("i");
      removeIcon.className = "bi bi-x-lg";
      removeBtn.appendChild(removeIcon);

      item.appendChild(img);
      item.appendChild(removeBtn);

      if (idx === 0) {
        const badge = document.createElement("span");
        badge.className = "cover-badge";
        badge.textContent = "Cover";
        item.appendChild(badge);
      }
      previewGrid.appendChild(item);
    });
  }

  // Add selected/dropped files to local state with a preview — NO upload yet.
  function addFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    for (const file of files) {
      if (!file.type || !file.type.startsWith("image/")) {
        toast(file.name + ": only image files are allowed.", "error");
        continue;
      }
      if (file.size > MAX_IMAGE_BYTES) {
        toast(file.name + ": image exceeds 10 MB.", "error");
        continue;
      }
      if (items.length >= MAX_IMAGES) {
        toast("You can add a maximum of 15 images.", "error");
        break;
      }
      items.push({ url: null, file: file, preview: URL.createObjectURL(file) });
    }
    if (imageInput) imageInput.value = "";
    renderPreviews();
  }

  // Upload any pending files to Cloudinary and return the ordered list of URLs.
  async function resolveImages() {
    const pending = items.filter(function (i) { return i.file; });
    let uploaded = [];
    if (pending.length) {
      const fd = new FormData();
      pending.forEach(function (i) { fd.append("files", i.file); });
      const res = await API.post("/api/uploads/images", fd);
      uploaded = Array.isArray(res.urls) ? res.urls : [];
    }
    let u = 0;
    const finalUrls = [];
    items.forEach(function (it) {
      if (it.file) {
        if (u < uploaded.length) finalUrls.push(uploaded[u++]);
      } else if (it.url) {
        finalUrls.push(it.url);
      }
    });
    return finalUrls;
  }

  if (uploader) {
    uploader.addEventListener("click", function (e) {
      if (e.target.closest("[data-remove-image]")) return;
      if (imageInput) imageInput.click();
    });
    uploader.addEventListener("dragover", function (e) {
      e.preventDefault();
      uploader.classList.add("dragover");
    });
    uploader.addEventListener("dragleave", function () {
      uploader.classList.remove("dragover");
    });
    uploader.addEventListener("drop", function (e) {
      e.preventDefault();
      uploader.classList.remove("dragover");
      addFiles(e.dataTransfer.files);
    });
  }

  if (imageInput) {
    imageInput.addEventListener("change", function () {
      addFiles(imageInput.files);
    });
  }

  if (previewGrid) {
    previewGrid.addEventListener("click", function (e) {
      const btn = e.target.closest("[data-remove-image]");
      if (!btn) return;
      const idx = parseInt(btn.dataset.removeImage, 10);
      if (!isNaN(idx) && idx >= 0 && idx < items.length) {
        const removed = items.splice(idx, 1)[0];
        if (removed && removed.file && removed.preview) URL.revokeObjectURL(removed.preview);
        renderPreviews();
      }
    });
  }

  renderPreviews();

  // Commercial listings don't need bedrooms/bathrooms in the same way.
  function syncListingFields() {
    const commercial = listingType?.value === "commercial";
    document.querySelectorAll("[data-bhk-field]").forEach((el) => {
      el.classList.toggle("hidden", commercial && el.dataset.bhkField === "bedrooms");
    });
    const priceLabel = document.querySelector("[data-price-label]");
    if (priceLabel) priceLabel.textContent = listingType?.value === "rent" ? "Monthly rent (₹)" : "Expected price (₹)";
    const rentFields = document.querySelectorAll("[data-rent-only]");
    rentFields.forEach((el) => el.classList.toggle("hidden", listingType?.value !== "rent"));
    document.querySelectorAll("[data-sale-only]").forEach((el) => {
      el.classList.toggle("hidden", listingType?.value === "rent");
    });
  }

  // Show/hide property types relevant to the chosen listing type.
  const TYPES = {
    buy: ["apartment", "independent-house", "villa", "builder-floor", "plot"],
    rent: ["apartment", "independent-house", "villa", "builder-floor", "studio", "pg-hostel"],
    commercial: ["office", "shop", "warehouse", "plot"],
  };
  function syncTypes() {
    if (!propType) return;
    const allowed = TYPES[listingType?.value] || [];
    const current = propType.value;
    Array.from(propType.options).forEach((opt) => {
      if (!opt.value) return;
      opt.hidden = !allowed.includes(opt.value);
      opt.disabled = !allowed.includes(opt.value);
    });
    if (!allowed.includes(current) && allowed.length) propType.value = allowed[0];
  }

  listingType?.addEventListener("change", () => { syncTypes(); syncListingFields(); });
  syncTypes();
  syncListingFields();

  // Live AI estimate
  const estBtn = document.getElementById("estimateBtn");
  estBtn?.addEventListener("click", async () => {
    const area = Number(form.querySelector("[name=area_sqft]")?.value || 0);
    if (!area) return toast("Enter the area first.", "error");
    estBtn.disabled = true;
    const original = estBtn.innerHTML;
    estBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Estimating…';
    try {
      const payload = {
        area: Math.round(area),
        bedrooms: Math.max(1, Number(form.querySelector("[name=bedrooms]")?.value || 1)),
        bathrooms: Math.max(1, Number(form.querySelector("[name=bathrooms]")?.value || 1)),
        stories: Math.max(1, Number(form.querySelector("[name=total_floors]")?.value || 1)),
        parking: 1,
        mainroad: true,
        airconditioning: form.querySelector("[name=furnishing]")?.value === "furnished",
        prefarea: true,
        furnishingstatus: form.querySelector("[name=furnishing]")?.value || "semi-furnished",
      };
      const res = await API.post("/api/ml/predict", payload);
      const box = document.getElementById("estimateBox");
      if (box) {
        box.innerHTML = `<div class="estimate-value">${res.price_label}</div>
          <div class="muted small">Expected range: <b>${res.range_label}</b> · model R² ≈ ${((window.NESTQUEST_METRICS?.linear_regression?.r2 || 0) * 100).toFixed(0)}%</div>`;
        box.classList.remove("hidden");
      }
    } catch (err) {
      toast(err.message, "error");
    } finally {
      estBtn.disabled = false;
      estBtn.innerHTML = original;
    }
  });

  // Submit
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const alertBox = document.getElementById("formAlert");
    const submitBtn = form.querySelector("[type=submit]");
    submitBtn.disabled = true;
    const original = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving…';

    const fd = new FormData(form);
    const amenities = Array.from(form.querySelectorAll("[name=amenities]:checked")).map((c) => c.value);

    const num = (k, d = 0) => (fd.get(k) === "" || fd.get(k) === null ? d : Number(fd.get(k)));
    try {
      if (items.some((i) => i.file)) {
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Uploading images…';
      }
      const images = await resolveImages();
      submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving…';

      const payload = {
        title: (fd.get("title") || "").trim(),
        description: (fd.get("description") || "").trim(),
        listing_type: fd.get("listing_type"),
        property_type: fd.get("property_type"),
        price: num("price"),
        area_sqft: num("area_sqft"),
        bedrooms: num("bedrooms"),
        bathrooms: num("bathrooms"),
        balconies: num("balconies"),
        floor: (fd.get("floor") || "").trim() || null,
        total_floors: fd.get("total_floors") ? num("total_floors") : null,
        furnishing: fd.get("furnishing"),
        facing: fd.get("facing") || null,
        age_years: fd.get("age_years") ? num("age_years") : null,
        city: (fd.get("city") || "").trim(),
        locality: (fd.get("locality") || "").trim(),
        address: (fd.get("address") || "").trim(),
        pincode: (fd.get("pincode") || "").trim() || null,
        contact_name: (fd.get("contact_name") || "").trim() || null,
        contact_phone: (fd.get("contact_phone") || "").trim() || null,
        amenities,
        images,
      };

      const res = isEdit
        ? await API.put(`/api/properties/${id}`, payload)
        : await API.post("/api/properties", payload);
      toast(res.message || "Saved!", "success");
      setTimeout(() => { window.location.href = `/property/${res.property.id}`; }, 700);
    } catch (err) {
      if (alertBox) {
        alertBox.className = "alert error";
        alertBox.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${err.message}`;
        alertBox.classList.remove("hidden");
        alertBox.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        toast(err.message, "error");
      }
      submitBtn.disabled = false;
      submitBtn.innerHTML = original;
    }
  });
}

/* ---------- Auth forms ---------- */
function initAuthForms() {
  const signup = document.getElementById("signupForm");
  signup?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(signup);
    const btn = signup.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await API.post("/api/auth/signup", {
        name: (fd.get("name") || "").trim(),
        email: (fd.get("email") || "").trim(),
        password: fd.get("password"),
        phone: (fd.get("phone") || "").trim() || null,
      });
      toast("Account created! Welcome 🎉", "success");
      const next = signup.dataset.next || "/dashboard";
      setTimeout(() => { window.location.href = next; }, 600);
    } catch (err) {
      showFormError("signupAlert", err.message);
      btn.disabled = false;
    }
  });

  const login = document.getElementById("loginForm");
  login?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(login);
    const btn = login.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await API.post("/api/auth/login", {
        email: (fd.get("email") || "").trim(),
        password: fd.get("password"),
      });
      toast("Logged in successfully.", "success");
      const next = login.dataset.next || "/dashboard";
      setTimeout(() => { window.location.href = next; }, 500);
    } catch (err) {
      showFormError("loginAlert", err.message);
      btn.disabled = false;
    }
  });
}

function showFormError(id, message) {
  const el = document.getElementById(id);
  if (!el) return toast(message, "error");
  el.className = "alert error";
  el.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${message}`;
  el.classList.remove("hidden");
}

/* ---------- Enquiry modal ---------- */
function initEnquiry() {
  const form = document.getElementById("enquiryForm");
  if (!form) return;
  const modal = document.getElementById("enquiryModal");
  document.querySelectorAll("[data-enquire]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!window.NESTQUEST_AUTH) return requireLogin("Log in to contact the owner.");
      form.dataset.property = btn.dataset.enquire;
      document.getElementById("enquiryProperty").textContent = btn.dataset.title || "";
      modal?.classList.remove("hidden");
      modal?.classList.add("open");
    });
  });
  document.querySelectorAll("[data-close-modal]").forEach((el) => {
    el.addEventListener("click", () => { modal?.classList.add("hidden"); modal?.classList.remove("open"); });
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const btn = form.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await API.post("/api/enquiries", {
        property_id: form.dataset.property,
        message: (fd.get("message") || "").trim(),
        phone: (fd.get("phone") || "").trim() || null,
      });
      toast("Enquiry sent! The owner will contact you.", "success");
      form.reset();
      modal?.classList.add("hidden");
      modal?.classList.remove("open");
    } catch (err) {
      toast(err.message, "error");
    } finally { btn.disabled = false; }
  });
}

/* ---------- Dashboard: delete listing, reply to enquiry ---------- */
function initDashboard() {
  document.addEventListener("click", async (e) => {
    const del = e.target.closest("[data-delete]");
    if (del) {
      if (!confirm("Delete this listing permanently?")) return;
      try {
        await API.del(`/api/properties/${del.dataset.delete}`);
        toast("Listing deleted.", "success");
        setTimeout(() => window.location.reload(), 500);
      } catch (err) { toast(err.message, "error"); }
    }

    const replyToggle = e.target.closest("[data-reply-toggle]");
    if (replyToggle) {
      const box = document.getElementById(`reply-${replyToggle.dataset.replyToggle}`);
      box?.classList.toggle("hidden");
    }

    const profileToggle = e.target.closest("[data-profile-toggle]");
    if (profileToggle) {
      document.getElementById("profileForm")?.classList.toggle("hidden");
    }
  });

  document.querySelectorAll("[data-reply-form]").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const btn = form.querySelector("[type=submit]");
      btn.disabled = true;
      try {
        await API.post(`/api/enquiries/${form.dataset.replyForm}/reply`, { reply: (fd.get("reply") || "").trim() });
        toast("Reply sent.", "success");
        setTimeout(() => window.location.reload(), 600);
      } catch (err) { toast(err.message, "error"); btn.disabled = false; }
    });
  });

  const profileForm = document.getElementById("profileForm");
  profileForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(profileForm);
    const btn = profileForm.querySelector("[type=submit]");
    btn.disabled = true;
    try {
      await API.put("/api/auth/me", {
        name: (fd.get("name") || "").trim(),
        phone: (fd.get("phone") || "").trim() || null,
        about: (fd.get("about") || "").trim() || null,
      });
      toast("Profile updated.", "success");
      setTimeout(() => window.location.reload(), 600);
    } catch (err) { toast(err.message, "error"); btn.disabled = false; }
  });
}

/* ---------- Admin ---------- */
function initAdmin() {
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-status]");
    if (btn) {
      const { status, id, featured } = btn.dataset;
      const body = { status };
      if (featured !== undefined) body.featured = featured === "true";
      try {
        const res = await API.patch(`/api/properties/${id}/status`, body);
        toast(res.message, "success");
        setTimeout(() => window.location.reload(), 500);
      } catch (err) { toast(err.message, "error"); }
    }

    const delUser = e.target.closest("[data-del-user]");
    if (delUser) {
      if (!confirm("Delete this user and all their listings?")) return;
      try {
        const res = await API.del(`/api/admin/users/${delUser.dataset.delUser}`);
        toast(res.message, "success");
        setTimeout(() => window.location.reload(), 500);
      } catch (err) { toast(err.message, "error"); }
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initPropertyForm();
  initAuthForms();
  initEnquiry();
  initDashboard();
  initAdmin();
});
