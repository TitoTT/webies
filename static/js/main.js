const inicioPagina = Date.now();

// ── CSRF ────────────────────────────────────────────────
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ── FORMULARIO DE CONTACTO ──────────────────────────────
async function enviarFormularioContacto(e) {
  e.preventDefault();

  const boton = e.target.querySelector('button[type="submit"]');

  const nombre = document.getElementById('nombre').value.trim();
  const email = document.getElementById('email').value.trim();
  let motivo = document.getElementById('motivo').value || 'general';
  let mensaje = document.getElementById('mensaje').value.trim();

  if (motivo === 'carrera') {
    const carrera = document.getElementById('motivo_carrera')?.value || 'Consulta sobre una carrera';
    mensaje = `[${carrera}]\n\n${mensaje}`;
    motivo = 'general';
  }

  if (boton) boton.disabled = true; // evita enviar dos veces

  try {
    const respuesta = await fetch('/api/contacto/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({
        nombre, email, motivo, mensaje,
        // Anti-spam: campo trampa (debe ir vacío) y segundos desde que se abrió la página
        web: document.getElementById('contacto_sitio')?.value || '',
        segundos: Math.round((Date.now() - inicioPagina) / 1000)
      })
    });

    const resultado = await respuesta.json();

    if (resultado.ok) {
      document.getElementById('formContacto').style.display = 'none';
      document.getElementById('formOk').style.display = 'block';
    } else {
      alert('Error: ' + (resultado.error || 'no se pudo enviar la consulta'));
    }
  } catch (error) {
    console.error('Error al enviar la consulta:', error);
    alert('No se pudo enviar la consulta. Intentá de nuevo en unos minutos.');
  } finally {
    if (boton) boton.disabled = false;
  }
}

// ── MENÚ HAMBURGUESA ────────────────────────────────────
function toggleNav(forzarCierre = false) {
  const menu = document.getElementById('navLinks');
  const boton = document.querySelector('.hamburger');
  if (!menu) return;
  const abierto = forzarCierre === true ? false : !menu.classList.contains('abierto');
  menu.classList.toggle('abierto', abierto);
  // Le avisa a los lectores de pantalla si el menú está abierto o cerrado
  if (boton) boton.setAttribute('aria-expanded', String(abierto));
}

// El menú del celular se cierra con la tecla Escape y al elegir un link
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') toggleNav(true);
});
document.querySelectorAll('.nav-links a').forEach(a => {
  a.addEventListener('click', () => toggleNav(true));
});

// ── RESALTAR SECCIÓN ACTIVA EN EL NAV ───────────────────
const secciones = document.querySelectorAll('section[id]');
const links = document.querySelectorAll('.nav-links a');

window.addEventListener('scroll', () => {
  let actual = '';
  secciones.forEach(s => {
    if (window.scrollY >= s.offsetTop - 80) actual = s.id;
  });
  links.forEach(l => {
    // Solo resaltamos links que apuntan a ESTA misma página
    const activo = l.pathname === window.location.pathname && l.hash === '#' + actual;
    l.style.borderBottomColor = activo ? 'var(--dorado)' : 'transparent';
    l.style.color = activo ? 'var(--dorado-cl)' : '';
  });
});