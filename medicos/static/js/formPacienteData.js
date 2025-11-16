// Archivo: static/js/formPacienteData.js
// Unifica la lógica de Alpine.js para formularios de paciente
// options: {
//   initial: { rut, nombre, correo, telefono, direccion, comentario, ... },
//   pacienteId: string|null,
//   criteriosClinicos: bool,
//   criteriosSociales: bool,
//   ejesClinicos: array,
//   ejesSociales: array
// }
function formPacienteData(options = {}) {
    const initial = options.initial || {};
    return {
        rut: initial.rut || '',
        rutError: '',
        nombre: initial.nombre || '',
        correo: initial.correo || '',
        telefono: initial.telefono || '',
        direccion: initial.direccion || '',
        comentario: initial.comentario || '',
        nombreError: '',
        correoError: '',
        telefonoError: '',
        direccionError: '',
        comentarioError: '',
        criteriosClinicos: {},
        criteriosSociales: {},
        ejesClinicos: options.ejesClinicos || [],
        ejesSociales: options.ejesSociales || [],
        criteriosClinicosError: '',
        criteriosSocialesError: '',
        intentadoEnviar: false,
        init() {
            if (options.ejesClinicosDataId) {
                this.ejesClinicos = JSON.parse(document.getElementById(options.ejesClinicosDataId).textContent);
            }
            if (options.ejesSocialesDataId) {
                this.ejesSociales = JSON.parse(document.getElementById(options.ejesSocialesDataId).textContent);
            }
        },
        cleanRut(rut) {
            return rut.replace(/[^0-9kK]/g, '').toUpperCase();
        },
        validateRut() {
            let rut = this.cleanRut(this.rut);
            if (rut.length < 2) {
                this.rutError = 'RUT muy corto';
                return false;
            }
            let cuerpo = rut.slice(0, -1);
            let dv = rut.slice(-1);
            let suma = 0;
            let multiplo = 2;
            for (let i = cuerpo.length - 1; i >= 0; i--) {
                suma += parseInt(cuerpo[i]) * multiplo;
                multiplo = multiplo < 7 ? multiplo + 1 : 2;
            }
            let dvEsperado = 11 - (suma % 11);
            dvEsperado = dvEsperado === 11 ? '0' : dvEsperado === 10 ? 'K' : dvEsperado.toString();
            if (dvEsperado !== dv) {
                this.rutError = 'RUT inválido';
                return false;
            }
            // Validación de existencia en backend
            let pacienteId = options.pacienteId || '';
            fetch(`/rut-exists?rut=${encodeURIComponent(rut)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.exists) {
                        if (data.id && pacienteId && data.id.toString() === pacienteId.toString()) {
                            this.rutError = '';
                        } else {
                            if (data.id) {
                                this.rutError = `Este RUT ya está registrado. <a href='/patients/detail/${data.id}/' target='_blank'>Ver detalle</a>`;
                            } else {
                                this.rutError = 'Este RUT ya está registrado.';
                            }
                        }
                    } else {
                        this.rutError = '';
                    }
                })
                .catch(() => {
                    this.rutError = 'Error al validar RUT en la base de datos';
                });
            return true;
        },
        validateNombre() {
            this.nombreError = (/^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(this.nombre) && this.nombre.trim() !== '') ? '' : 'Solo letras permitidas y obligatorio';
            return this.nombreError === '';
        },
        validateCorreo() {
            const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            if (this.correo.trim() === '') {
                this.correoError = '';
                return true;
            }
            this.correoError = re.test(this.correo) ? '' : 'Correo inválido';
            return this.correoError === '';
        },
        validateTelefono() {
            if (this.telefono.trim() === '') {
                this.telefonoError = '';
                return true;
            }
            const re = /^\+?1?\d{9,15}(;\s*\+?1?\d{9,15})*$/;
            this.telefonoError = re.test(this.telefono) ? '' : 'Teléfono inválido';
            return this.telefonoError === '';
        },
        validateDireccion() {
            this.direccionError = '';
            return true;
        },
        validateComentario() {
            this.comentarioError = this.comentario.trim() !== '' ? '' : 'Campo obligatorio';
            return this.comentarioError === '';
        },
        validateCriteriosClinicos() {
            if (!options.criteriosClinicos) return true;
            let valid = true;
            for (let eje of this.ejesClinicos) {
                if (!this.criteriosClinicos[eje]) {
                    valid = false;
                    break;
                }
            }
            this.criteriosClinicosError = valid ? '' : 'Debe seleccionar un criterio en cada eje clínico';
            return valid;
        },
        validateCriteriosSociales() {
            if (!options.criteriosSociales) return true;
            let valid = true;
            for (let eje of this.ejesSociales) {
                if (!this.criteriosSociales[eje]) {
                    valid = false;
                    break;
                }
            }
            this.criteriosSocialesError = valid ? '' : 'Debe seleccionar un criterio en cada eje social';
            return valid;
        },
        validateAll() {
            this.intentadoEnviar = true;
            let valid = true;
            valid = this.validateNombre() && valid;
            valid = this.validateCorreo() && valid;
            valid = this.validateTelefono() && valid;
            valid = this.validateDireccion() && valid;
            valid = this.validateComentario() && valid;
            if (options.criteriosClinicos) valid = this.validateCriteriosClinicos() && valid;
            if (options.criteriosSociales) valid = this.validateCriteriosSociales() && valid;
            return valid;
        },
        handleSubmit(event) {
            if (this.validateAll()) {
                event.target.submit();
            }
        }
    }
}

// Para uso con Alpine.js: window.formPacienteData = formPacienteData;
window.formPacienteData = formPacienteData;
