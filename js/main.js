function toggleSidebar() {
  document.getElementById('sidebar')?.classList.toggle('open');
}
document.addEventListener('click', function(e) {
  const sidebar = document.getElementById('sidebar');
  const hamburger = document.getElementById('hamburger');
  if (!sidebar || !hamburger) return;
  if (!sidebar.contains(e.target) && !hamburger.contains(e.target))
    sidebar.classList.remove('open');
});
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.alert').forEach(function(a) {
    setTimeout(function() {
      a.style.transition = 'opacity .4s';
      a.style.opacity = '0';
      setTimeout(() => a.remove(), 400);
    }, 4500);
  });
});
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') document.getElementById('deleteModal')?.classList.remove('active');
});
document.addEventListener('click', function(e) {
  const m = document.getElementById('deleteModal');
  if (m && e.target === m) m.classList.remove('active');
});
function confirmDelete(id, name) {
  document.getElementById('deleteName').textContent = name;
  document.getElementById('deleteForm').action = '/delete/' + id;
  document.getElementById('deleteModal').classList.add('active');
}
function closeModal() {
  document.getElementById('deleteModal')?.classList.remove('active');
}
