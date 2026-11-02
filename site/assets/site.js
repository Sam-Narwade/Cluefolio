(function () {
  var lb = document.getElementById("lightbox");
  if (!lb) return;

  var lbImg = lb.querySelector("img");
  var imgs = Array.prototype.slice.call(document.querySelectorAll(".carousel img"));
  var current = -1;

  function open(index) {
    if (index < 0 || index >= imgs.length) return;
    current = index;
    var img = imgs[index];
    lbImg.src = img.getAttribute("data-full") || img.src;
    lbImg.alt = img.alt;
    lb.classList.add("open");
  }

  function close() {
    lb.classList.remove("open");
    lbImg.removeAttribute("src");
    current = -1;
  }

  imgs.forEach(function (img, i) {
    img.addEventListener("click", function () {
      open(i);
    });
  });

  lb.addEventListener("click", function (e) {
    if (e.target === lb || e.target.classList.contains("close")) close();
  });

  document.addEventListener("keydown", function (e) {
    if (!lb.classList.contains("open")) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowRight") open(current + 1);
    if (e.key === "ArrowLeft") open(current - 1);
  });
})();
