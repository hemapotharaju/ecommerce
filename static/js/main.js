// live search suggestions + auto-hide flashes
var box = document.getElementById('searchBox'), sug = document.getElementById('suggest');
if (box) {
  box.addEventListener('input', function () {
    var q = box.value.trim();
    if (q.length < 2) { sug.innerHTML = ''; return; }
    fetch('/api/search?q=' + encodeURIComponent(q)).then(function (r) { return r.json(); }).then(function (rows) {
      sug.innerHTML = rows.map(function (p) {
        return '<a href="/product/' + p.id + '"><img src="' + (p.image_url || '') + '"><span>' + p.name + ' — ₹' + p.price + '</span></a>';
      }).join('');
    });
  });
  document.addEventListener('click', function (e) { if (e.target !== box) sug.innerHTML = ''; });
}
setTimeout(function () { document.querySelectorAll('.flash').forEach(function (f) { f.style.display = 'none'; }); }, 3500);
