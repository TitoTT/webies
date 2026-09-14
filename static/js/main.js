// ── CARGA DE NOTICIAS (API) ─────────────────────────────
async function cargarNoticias() {
  try {
    // 1. Pedir los datos a la API
    const respuesta = await fetch('/api/noticias/');
    
    // 2. Convertir la respuesta a JSON
    const noticias = await respuesta.json();
    
    // 3. Renderizar las noticias
    renderizarNoticias(noticias);
    
  } catch (error) {
    console.error('Error al cargar noticias:', error);
    document.getElementById('noticiasGrid').innerHTML = 
      '<p>Error al cargar las noticias. Intentá más tarde.</p>';
  }
}

// Función para renderizar las Noticias en el HTML
function renderizarNoticias(noticias) {
  const gridNoticias = document.getElementById('noticiasGrid');
  gridNoticias.innerHTML = ''; 
  
  noticias.forEach(n => {
    // Solo cambiá 'n' por la variable que viene del fetch
    gridNoticias.innerHTML += `
      <div class="noticia-card">
        <div class="noticia-img" style="background-image: url('/static/${n.imagen}')"></div>
        <div class="noticia-body">
          <div class="noticia-cat">${n.categoria}</div>
          <h3>${n.titulo}</h3>
          <p>${n.texto}</p>
          <span class="noticia-fecha">📅 ${n.fecha}</span>
        </div>
      </div>`;
  });
}


// ── CARGA DE CARRERAS (API) ─────────────────────────────
async function cargarCarreras() {
  try {
    // 1. Pedir los datos a la API
    const respuesta = await fetch('/api/carreras/');
    
    // 2. Convertir la respuesta a JSON
    const carreras = await respuesta.json();
    
    // 3. Llamamos a la función que pinta las tarjetas
    renderizarCarreras(carreras);
    
  } catch (error) {
    console.error('Error al cargar carreras:', error);
    document.getElementById('carrerasGrid').innerHTML = 
      '<p>Error al cargar las carreras.</p>';
  }
}

// Función para pintar las tarjetas (la lógica visual)
function renderizarCarreras(carreras) {
  const gridCarreras = document.getElementById('carrerasGrid');
  gridCarreras.innerHTML = ''; // Limpiamos por si acaso
  
  carreras.forEach((c, i) => {
    // Aquí construimos la URL de la imagen
    // Si la carrera tiene imagen, usamos '/static/...', si no, usamos el color azul por defecto
    let urlImagen = '/static/' + c.imagen;
    
    // Si la imagen no existe o está vacía, usamos un color de fondo o un placeholder
    // (Ajustá esto si tu modelo de carreras no tiene campo imagen)
    if (!c.imagen || c.imagen.trim() === '') {
        urlImagen = 'var(--azul-med)'; // Color azul por defecto
    }

    // Generamos el HTML de la tarjeta
    const materiasTexto = c.materias.join(', '); // Si la API devuelve una lista
    
    gridCarreras.innerHTML += `
      <div class="carrera-card" onclick="abrirModal(${i})">
        <div class="carrera-icono" style="background-image: url('${urlImagen}'); background-size: cover; background-position: center;"></div>
        <h3>${c.nombre}</h3>
        <p>${c.descripcion}</p>
        <span class="carrera-duracion">⏱ Duración: ${c.duracion} &nbsp;›&nbsp; Ver materias</span>
      </div>`;
  });
}

// Esta función es la que se ejecuta cuando la página carga
document.addEventListener('DOMContentLoaded', () => {
  cargarNoticias();  
  cargarCarreras();  
  cargarAutoridades();
  cargarMapa();
});


// ── CARGA DE AUTORIDADES (API) ───────────────────────────
  async function cargarAutoridades() {
  try {
    const respuesta = await fetch('/api/autoridades/');
    const autoridades = await respuesta.json();
    renderizarAutoridades(autoridades);
  } catch (error) {
    console.error('Error al cargar autoridades:', error);
    document.getElementById('autoridadesGrid').innerHTML = '<p>Error al cargar las autoridades.</p>';
  }
}

function renderizarAutoridades(autoridades) {
  const gridAut = document.getElementById('autoridadesGrid');
  gridAut.innerHTML = '';

  autoridades.forEach(a => {
    gridAut.innerHTML += `
      <div class="autoridad-card">
        <div class="autoridad-avatar">${a.iniciales}</div>
        <h3>${a.nombre}</h3>
        <p>${a.cargo}</p>
      </div>`;
  });
}

  // ── MODAL ──────────────────────────────────────────────
  function abrirModal(i) {
    const c = carreras[i];
    document.getElementById('modalTitulo').textContent = c.nombre;
    document.getElementById('modalDescripcion').textContent = c.descripcion;
    document.getElementById('modalMaterias').innerHTML =
      c.materias.map(m => `<li>${m}</li>`).join('');
    document.getElementById('modalOverlay').classList.add('activo');
  }

  function cerrarModal(e) {
    if (!e || e.target === document.getElementById('modalOverlay') || !e.target) {
      document.getElementById('modalOverlay').classList.remove('activo');
    }
  }

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') cerrarModal();
  });


// Función para obtener el token CSRF de la cookie
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


  // ── FORMULARIO ────────────────────────────────────────
async function enviarFormularioContacto(e) {
  e.preventDefault(); // ¡MUY IMPORTANTE! Evita el envío tradicional

  console.log("Intentando enviar formulario...");

  // 1. Obtener valores
  const nombre = document.getElementById('nombre').value;
  const email = document.getElementById('email').value;
  const motivo = document.getElementById('motivo').value;
  const mensaje = document.getElementById('mensaje').value;

  const datos = {
    nombre: nombre,
    email: email,
    motivo: motivo,
    mensaje: mensaje
  };

  console.log("Datos a enviar:", datos);

  const csrftoken = getCookie('csrftoken');

  try {
    console.log("Enviando a /api/contacto/ con método POST..."); // <--

    // 2. LA PETICIÓN DEBE SER POST
    const respuesta = await fetch('/api/contacto/', {
      method: 'POST', // <--- ESTO ES CRUCIAL
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify(datos)
    });


    console.log("Respuesta recibida:", respuesta);
    const resultado = await respuesta.json();
    console.log("Resultado final:", resultado); // <-- Para depurar

    if (resultado.ok) {
      // Éxito
      document.getElementById('formContacto').style.display = 'none';
      document.getElementById('formOk').style.display = 'block';
    } else {
      // Error
      alert('Error: ' + resultado.error);
    }
  } catch (error) {
    console.error('Error de red:', error);
    alert('Error de conexión');
  }
}

async function cargarMapa() {
  try {
    const respuesta = await fetch('/api/config/');
    const config = await respuesta.json();
    
    if (config.url_mapa) {
      // Cargar el iframe
      document.getElementById('mapa-container').innerHTML = `
        <iframe 
          src="${config.url_mapa}" 
          width="100%" 
          height="350" 
          style="border:0;" 
          allowfullscreen="" 
          loading="lazy" 
          referrerpolicy="no-referrer-when-downgrade">
        </iframe>
      `;
      
      // Actualizar textos de contacto
      document.getElementById('direccion-texto').textContent = config.direccion || 'Av. Hipólito Yrigoyen 351, Trancas, Tucumán';
      document.getElementById('email-texto').textContent = config.email || 'ies@sanpedro.edu.ar';
      document.getElementById('horario-texto').textContent = config.horario || 'Lun–Vie: 17:00 a 21:30';
    }
  } catch (error) {
    console.error('Error al cargar el mapa:', error);
  }
}


  // ── HAMBURGER ─────────────────────────────────────────
  function toggleNav() {
    document.getElementById('navLinks').classList.toggle('abierto');
  }

  // ── SCROLL ACTIVO NAV ─────────────────────────────────
  const secciones = document.querySelectorAll('section[id], div[id]');
  const links = document.querySelectorAll('.nav-links a');

// ── INICIALIZACIÓN ───────────────────────────────────────
  // SOLO UN EVENT LISTENER
  document.addEventListener('DOMContentLoaded', () => {
    cargarNoticias();
    cargarCarreras();
    cargarAutoridades(); 
  });

  window.addEventListener('scroll', () => {
    let actual = '';
    secciones.forEach(s => {
      if (window.scrollY >= s.offsetTop - 80) actual = s.getAttribute('id');
    });
    links.forEach(l => {
      l.style.borderBottomColor = l.getAttribute('href') === '#' + actual ? 'var(--dorado)' : 'transparent';
      l.style.color = l.getAttribute('href') === '#' + actual ? 'var(--dorado-cl)' : '';
    });
  });