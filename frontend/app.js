// CampusCare frontend — talks to the FastAPI backend on the same origin.
// Token note: stored in localStorage for simplicity. For production, prefer an
// httpOnly cookie so XSS can't read the token.

const TOKEN_KEY = "cc_token";
const token = () => localStorage.getItem(TOKEN_KEY);
const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
const clearToken = () => localStorage.removeItem(TOKEN_KEY);

const $ = (sel) => document.querySelector(sel);

async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && token()) headers["Authorization"] = `Bearer ${token()}`;
  const res = await fetch(path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Something went wrong");
  return data;
}

// ---- view switching -------------------------------------------------
function showApp() {
  $("#auth-view").classList.add("hidden");
  $("#app-view").classList.remove("hidden");
  $("#logout").classList.remove("hidden");
  loadNotes();
}
function showAuth() {
  $("#app-view").classList.add("hidden");
  $("#auth-view").classList.remove("hidden");
  $("#logout").classList.add("hidden");
  $("#messages").innerHTML = "";
}

// ---- auth -----------------------------------------------------------
document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
    t.classList.add("active");
    const login = t.dataset.tab === "login";
    $("#login-form").classList.toggle("hidden", !login);
    $("#register-form").classList.toggle("hidden", login);
    $("#auth-error").textContent = "";
  })
);

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const d = formData(e.target);
    const r = await api("/auth/login", { method: "POST", auth: false,
      body: { email: d.email, password: d.password } });
    setToken(r.access_token);
    showApp();
  } catch (err) { $("#auth-error").textContent = err.message; }
});

$("#register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const d = formData(e.target);
    const r = await api("/auth/register", { method: "POST", auth: false,
      body: { email: d.email, password: d.password, display_name: d.display_name || "" } });
    setToken(r.access_token);
    showApp();
  } catch (err) { $("#auth-error").textContent = err.message; }
});

$("#logout").addEventListener("click", () => { clearToken(); showAuth(); });

// ---- chat -----------------------------------------------------------
function bubble(text, cls) {
  const el = document.createElement("div");
  el.className = `msg ${cls}`;
  el.textContent = text;
  $("#messages").appendChild(el);
  $("#messages").scrollTop = $("#messages").scrollHeight;
}

function crisisCard(reply, resources) {
  const el = document.createElement("div");
  el.className = "msg crisis";
  const h = document.createElement("h3");
  h.textContent = "Please reach out for support";
  el.appendChild(h);
  const p = document.createElement("div");
  p.textContent = reply;
  el.appendChild(p);
  const ul = document.createElement("ul");
  ul.className = "resources";
  resources.forEach((r) => {
    const li = document.createElement("li");
    const name = document.createElement("div"); name.className = "name"; name.textContent = r.name;
    const c = document.createElement("div"); c.className = "contact"; c.textContent = r.contact;
    li.append(name, c);
    if (r.note) { const n = document.createElement("div"); n.className = "note"; n.textContent = r.note; li.appendChild(n); }
    ul.appendChild(li);
  });
  el.appendChild(ul);
  $("#messages").appendChild(el);
  $("#messages").scrollTop = $("#messages").scrollHeight;
}

function elevatedCard(resources) {
  const el = document.createElement("div");
  el.className = "msg elevated";
  const p = document.createElement("div");
  p.textContent = "If it would help, these are here for you any time:";
  el.appendChild(p);
  const ul = document.createElement("ul");
  ul.className = "resources";
  resources.forEach((r) => {
    const li = document.createElement("li");
    const name = document.createElement("div"); name.className = "name"; name.textContent = r.name;
    const c = document.createElement("div"); c.className = "contact"; c.textContent = r.contact;
    li.append(name, c);
    ul.appendChild(li);
  });
  el.appendChild(ul);
  $("#messages").appendChild(el);
  $("#messages").scrollTop = $("#messages").scrollHeight;
}

$("#chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#chat-text");
  const text = input.value.trim();
  if (!text) return;
  bubble(text, "user");
  input.value = "";
  try {
    const r = await api("/chat", { method: "POST", body: { message: text } });
    if (r.crisis_detected) {
      crisisCard(r.reply, r.resources || []);
    } else {
      bubble(r.reply, "bot");
      if (r.elevated && (r.resources || []).length) elevatedCard(r.resources);
    }
  } catch (err) {
    if (/auth/i.test(err.message) || /token/i.test(err.message)) return showAuth();
    bubble("Sorry — I couldn't respond just now. Please try again.", "bot");
  }
});

// ---- notes ----------------------------------------------------------
async function loadNotes() {
  try {
    const notes = await api("/notes");
    const list = $("#note-list");
    list.innerHTML = "";
    notes.forEach((n) => {
      const item = document.createElement("div");
      item.className = "note-item";
      const row = document.createElement("div"); row.className = "row";
      const title = document.createElement("div"); title.className = "nt"; title.textContent = n.title;
      const del = document.createElement("button"); del.className = "del"; del.textContent = "Delete";
      del.addEventListener("click", async () => { await api(`/notes/${n.id}`, { method: "DELETE" }); loadNotes(); });
      row.append(title, del);
      const body = document.createElement("div"); body.className = "nx"; body.textContent = n.text;
      item.append(row, body);
      list.appendChild(item);
    });
  } catch (err) { if (/auth|token/i.test(err.message)) showAuth(); }
}

$("#note-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const d = formData(e.target);
  try {
    await api("/notes", { method: "POST", body: { title: d.title || "Untitled", text: d.text || "" } });
    e.target.reset();
    loadNotes();
  } catch (err) { if (/auth|token/i.test(err.message)) showAuth(); }
});

// ---- boot -----------------------------------------------------------
if (token()) showApp(); else showAuth();
