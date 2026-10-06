const $ = (selector) => document.querySelector(selector);
let csrfToken = "";
async function api(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  if (!["GET", "HEAD"].includes(method) && !["/api/auth/login", "/api/auth/register"].includes(url)) {
    if (!csrfToken) csrfToken = (await fetch("/api/auth/csrf").then((r) => r.json())).csrf_token;
    options.headers = { ...(options.headers || {}), "X-CSRFToken": csrfToken };
  }
  const response = await fetch(url, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  let data = {}; try { data = await response.json(); } catch (_) {}
  if (!response.ok) throw Error(data.error || data.message || "Request failed");
  return data;
}
function logout() { api("/api/auth/logout", { method: "POST" }).then(() => { location = "/login"; }); }
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char])); }
async function loadBugs() {
  const data = await api("/api/bugs"); const bugs = data.items || [];
  const rows = bugs.map((bug) => `<div class="bug-row"><span>#${bug.id}</span><a href="/bugs/${bug.id}">${escapeHtml(bug.title)}</a><span class="badge ${bug.severity}">${bug.severity}</span><span class="badge ${bug.status}">${bug.status}</span></div>`).join("") || '<p class="muted">No bugs match the current filters.</p>';
  if ($("#bug-list")) $("#bug-list").innerHTML = rows;
  if ($("#recent")) { $("#recent").innerHTML = bugs.slice(0, 5).map((bug) => `<div class="bug-row"><a href="/bugs/${bug.id}">${escapeHtml(bug.title)}</a><span class="badge ${bug.severity}">${bug.severity}</span></div>`).join("") || '<p class="muted">No bugs yet.</p>'; $("#total").textContent = data.total || 0; $("#open").textContent = bugs.filter((bug) => bug.status === "OPEN").length; $("#critical").textContent = bugs.filter((bug) => bug.severity === "CRITICAL").length; $("#resolved").textContent = bugs.filter((bug) => bug.status === "RESOLVED").length; }
}
async function loadDetail(id) {
  const bug = await api(`/api/bugs/${id}`);
  $("#bug-detail").innerHTML = `<p class="eyebrow">Bug #${bug.id}</p><h1>${escapeHtml(bug.title)}</h1><p>${escapeHtml(bug.description)}</p><p><span class="badge ${bug.severity}">${bug.severity}</span> <span class="badge ${bug.status}">${bug.status}</span> · ${escapeHtml(bug.environment)}</p><hr><h2>AI analysis</h2><button id="analyze">Analyze bug</button><div id="analysis">${bug.analysis ? `<p>${escapeHtml(bug.analysis.summary)}</p><p><b>Possible cause:</b> ${escapeHtml(bug.analysis.possible_cause)}</p><p><b>Suggested fix:</b> ${escapeHtml(bug.analysis.suggested_fix)}</p>` : '<p class="muted">Optional AI analysis is not run yet.</p>'}</div><hr><h2>Comments</h2><div>${(bug.comments || []).map((comment) => `<p><b>${escapeHtml(comment.author)}</b>: ${escapeHtml(comment.content)}</p>`).join("") || '<p class="muted">No comments.</p>'}</div><form id="comment-form"><input name="content" placeholder="Add a comment" required><button>Add comment</button></form>`;
  $("#analyze").onclick = async () => { try { const analysis = await api(`/api/bugs/${id}/analyze`, { method: "POST" }); $("#analysis").innerHTML = `<p>${escapeHtml(analysis.summary)}</p><p><b>Possible cause:</b> ${escapeHtml(analysis.possible_cause)}</p><p><b>Suggested fix:</b> ${escapeHtml(analysis.suggested_fix)}</p>`; } catch (error) { $("#analysis").textContent = error.message; } };
  $("#comment-form").onsubmit = async (event) => { event.preventDefault(); const form = new FormData(event.target); await api(`/api/bugs/${id}/comments`, { method: "POST", body: JSON.stringify(Object.fromEntries(form)) }); loadDetail(id); };
}
async function init() {
  try { const user = await api("/api/auth/me"); if ($("#nav-user")) $("#nav-user").textContent = user.name; } catch (_) { if (!["/login", "/register"].includes(location.pathname)) location = "/login"; }
  if ($("#login-form")) $("#login-form").onsubmit = async (event) => { event.preventDefault(); try { await api("/api/auth/login", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(event.target))) }); location = "/dashboard"; } catch (error) { $("#message").textContent = error.message; } };
  if ($("#register-form")) $("#register-form").onsubmit = async (event) => { event.preventDefault(); try { await api("/api/auth/register", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(event.target))) }); location = "/dashboard"; } catch (error) { $("#message").textContent = error.message; } };
  if ($("#bug-list") || $("#recent")) loadBugs();
  if ($("#bug-detail")) loadDetail($("#bug-detail").dataset.id);
  if ($("#bug-form")) $("#bug-form").onsubmit = async (event) => { event.preventDefault(); try { const bug = await api("/api/bugs", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(event.target))) }); location = `/bugs/${bug.id}`; } catch (error) { $("#message").textContent = error.message; } };
}
init();
