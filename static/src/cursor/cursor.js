// Gradient màu cầu vồng (loại bỏ blue)
const gradients = [
    'linear-gradient(45deg, #FF0000, #FF7F00)', // đỏ → cam
    'linear-gradient(45deg, #FF7F00, #FFFF00)', // cam → vàng
    'linear-gradient(45deg, #FFFF00, #00FF00)', // vàng → lục
    'linear-gradient(45deg, #00FF00, #4B0082)', // lục → chàm
    'linear-gradient(45deg, #4B0082, #8F00FF)', // chàm → tím
    'linear-gradient(45deg, #FF0000, #8F00FF)'  // đỏ → tím
];

function spawnHeart(x, y) {
    const el = document.createElement('div');
    el.className = 'heart';
    el.textContent = '❤';

    // Random gradient
    const grad = gradients[(Math.random() * gradients.length) | 0];
    el.style.backgroundImage = grad;

    const dur = 900 + Math.random() * 700;
    const dx = (Math.random() - 0.5) * 120;
    el.style.setProperty('--dur', dur + 'ms');
    el.style.setProperty('--dx', dx + 'px');

    el.style.left = x + 'px';
    el.style.top = y + 'px';

    document.body.appendChild(el);
    el.addEventListener('animationend', () => el.remove());
}

document.addEventListener('click', (e) => {
  const tag = (e.target.tagName || '').toLowerCase();

  // Với link <a>, tạo tim rồi đi link
  if (tag === 'a') {
    e.preventDefault();
    spawnHeart(e.clientX, e.clientY);
    setTimeout(() => { window.location.href = e.target.href }, 300);
    return;
  }

  // Với button / input cũng cho tim xuất hiện
  spawnHeart(e.clientX, e.clientY);
}, { passive: true });
