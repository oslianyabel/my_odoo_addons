/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

publicWidget.registry.SignUpForm = publicWidget.Widget.extend({
    selector: '.oe_signup_form',
    events: {
        'submit': '_onSubmit',
        'input input[name="password"]': '_onPasswordInput',
        'input input[name="confirm_password"]': '_onConfirmPasswordInput',
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Real-time password validation feedback
     * @private
     */
    _onPasswordInput: function (ev) {
        var password = ev.target.value;
        this._updatePasswordRequirements(password);
    },

    /**
     * Confirm password validation
     * @private
     */
    _onConfirmPasswordInput: function (ev) {
        var passwordInput = this.el.querySelector('input[name="password"]');
        var confirmPassword = ev.target.value;
        var password = passwordInput ? passwordInput.value : '';
        
        if (confirmPassword && password !== confirmPassword) {
            ev.target.classList.add('is-invalid');
        } else {
            ev.target.classList.remove('is-invalid');
        }
    },

    /**
     * Update password requirements visual feedback
     * @private
     */
    _updatePasswordRequirements: function (password) {
        var requirements = this.el.querySelectorAll('.requirement');
        
        requirements.forEach(function(req) {
            var type = req.getAttribute('data-requirement');
            var icon = req.querySelector('i');
            var isValid = false;
            
            switch(type) {
                case 'length':
                    isValid = password.length >= 8 && password.length <= 12;
                    break;
                case 'uppercase':
                    isValid = /[A-Z]/.test(password);
                    break;
                case 'number':
                    isValid = /[0-9]/.test(password);
                    break;
                case 'special':
                    isValid = /[!@#$%^&*(),.?":{}|<>]/.test(password);
                    break;
            }
            
            if (isValid) {
                icon.className = 'fa fa-check text-success';
                req.classList.add('valid');
            } else {
                icon.className = 'fa fa-times text-danger';
                req.classList.remove('valid');
            }
        });
    },

    /**
     * @private
     */
    _onSubmit: function (ev) {
        ev.preventDefault();
        var self = this;
        
        // find name input (data-fill-with / name variants)
        var nameInput = this.el.querySelector('input[data-fill-with="name"]') || this.el.querySelector('input[name="name"]') || this.el.querySelector('input[name="Nombre"]');
        if (nameInput) {
            var val = nameInput.value.trim();
            if (val) {
                var valid = true;
                for (var i = 0; i < val.length; i++) {
                    var ch = val.charAt(i);
                    // allow letters, spaces, hyphen, apostrophe
                    if (!(/[\p{L}]/u.test(ch) || ch === ' ' || ch === '-' || ch === "'")) {
                        valid = false;
                        break;
                    }
                }
                if (!valid) {
                    // show error above form
                    this.$('.signup_error').remove();
                    var msg = _t('Por favor ingrese un nombre válido sin números ni caracteres especiales.');
                    this.$el.prepend('<div class="alert alert-danger signup_error" role="alert">' + msg + '</div>');
                    nameInput.focus();
                    return false;
                }
            }
        }
        // validate email (login) field
        var emailInput = this.el.querySelector('input[name="login"]') || this.el.querySelector('input[name="email"]');
        if (emailInput) {
            var email = emailInput.value.trim();
            if (email) {
                // basic email regex
                var emailRe = /^[\w-.]+@(?:[\w-]+\.)+[\w-]{2,}$/i;
                if (!emailRe.test(email)) {
                    this.$('.signup_error').remove();
                    var msgEmail = _t('Por favor ingrese un correo electrónico válido.');
                    this.$el.prepend('<div class="alert alert-danger signup_error" role="alert">' + msgEmail + '</div>');
                    emailInput.focus();
                    return false;
                }
            }
        }
        
        // validate password field
        var passwordInput = this.el.querySelector('input[name="password"]');
        var confirmPasswordInput = this.el.querySelector('input[name="confirm_password"]');
        if (passwordInput) {
            var password = passwordInput.value;
            var confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';
            
            // Password requirements validation
            var passwordErrors = [];
            
            // Length validation (8-12 characters)
            if (password.length < 8 || password.length > 12) {
                passwordErrors.push('La contraseña debe tener entre 8 y 12 caracteres');
            }
            
            // Uppercase letter validation
            if (!/[A-Z]/.test(password)) {
                passwordErrors.push('La contraseña debe contener al menos una letra mayúscula');
            }
            
            // Number validation
            if (!/[0-9]/.test(password)) {
                passwordErrors.push('La contraseña debe contener al menos un número');
            }
            
            // Special character validation
            if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
                passwordErrors.push('La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?":{}|<>)');
            }
            
            // Password confirmation validation
            if (confirmPassword && password !== confirmPassword) {
                passwordErrors.push('Las contraseñas no coinciden');
            }
            
            if (passwordErrors.length > 0) {
                this.$('.signup_error').remove();
                var errorMsg = '<ul class="mb-0">';
                passwordErrors.forEach(function(error) {
                    errorMsg += '<li>' + error + '</li>';
                });
                errorMsg += '</ul>';
                this.$el.prepend('<div class="alert alert-danger signup_error" role="alert">' + errorMsg + '</div>');
                passwordInput.focus();
                return false;
            }
        }
        
        var $btn = this.$('.oe_login_buttons > button[type="submit"]');
        $btn.attr('disabled', 'disabled');
        $btn.prepend('<i class="fa fa-refresh fa-spin"/> ');
        
        // Use AJAX to submit form and handle server errors
        var formData = new FormData(this.el);
        
        fetch(this.el.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(function(response) {
            console.log('Signup response status:', response.status);
            return response.text();
        })
        .then(function(html) {
            console.log('Signup response received, length:', html.length);
            
            // Parse the response to check for errors
            var parser = new DOMParser();
            var doc = parser.parseFromString(html, 'text/html');
            
            // Look for error in multiple places
            var errorElement = doc.querySelector('.alert-danger') || 
                             doc.querySelector('p[role="alert"]') ||
                             doc.querySelector('[class*="error"]');
            
            console.log('Error element found:', !!errorElement);
            
            if (errorElement) {
                // Server returned an error, display it
                console.log('Attempting to display error message');
                
                // Remove existing errors
                var existingErrors = self.el.querySelectorAll('.signup_error');
                existingErrors.forEach(function(err) { err.remove(); });
                
                var errorText = errorElement.textContent.trim();
                console.log('Error text:', errorText);
                
                if (errorText) {
                    // Show alert with error message
                    alert(errorText);
                    
                    // Create error div using vanilla JS for better compatibility
                    var errorDiv = document.createElement('div');
                    errorDiv.className = 'alert alert-danger signup_error';
                    errorDiv.setAttribute('role', 'alert');
                    errorDiv.textContent = errorText;
                    
                    // Insert at the beginning of the form
                    self.el.insertBefore(errorDiv, self.el.firstChild);
                    console.log('Error message inserted into DOM');
                    
                    // Re-enable button
                    $btn.removeAttr('disabled');
                    $btn.find('.fa-refresh').remove();
                    
                    // Scroll to error
                    setTimeout(function() {
                        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 100);
                } else {
                    console.warn('Error element found but no text content');
                    // Re-enable button
                    $btn.removeAttr('disabled');
                    $btn.find('.fa-refresh').remove();
                }
            } else {
                console.log('No error found, checking for success indicators');
                // Success - redirect or reload
                var successRedirect = doc.querySelector('meta[http-equiv="refresh"]');
                if (successRedirect) {
                    var content = successRedirect.getAttribute('content');
                    var urlMatch = content.match(/url=(.+)/);
                    if (urlMatch) {
                        window.location.href = urlMatch[1];
                    } else {
                        window.location.reload();
                    }
                } else {
                    // Check if we got redirected (different URL in response)
                    if (html.includes('account_created=1') || html.includes('login_success')) {
                        window.location.href = '/web/login?account_created=1';
                    } else {
                        console.log('No clear success indicator, submitting form normally');
                        // Fallback: submit form normally
                        self.el.submit();
                    }
                }
            }
        })
        .catch(function(error) {
            console.error('Error submitting form:', error);
            // Re-enable button
            $btn.removeAttr('disabled');
            $btn.find('.fa-refresh').remove();
            
            // Remove existing errors
            var existingErrors = self.el.querySelectorAll('.signup_error');
            existingErrors.forEach(function(err) { err.remove(); });
            
            // Show generic error using vanilla JS
            var errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger signup_error';
            errorDiv.setAttribute('role', 'alert');
            errorDiv.textContent = 'Error al procesar el formulario. Por favor, intente nuevamente.';
            self.el.insertBefore(errorDiv, self.el.firstChild);
        });
    },
});

publicWidget.registry.ResetPasswordForm = publicWidget.Widget.extend({
    selector: '.oe_reset_password_form',
    events: {
        'submit': '_onSubmit',
        'input input[name="password"]': '_onPasswordInput',
        'input input[name="confirm_password"]': '_onConfirmPasswordInput',
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Real-time password validation feedback
     * @private
     */
    _onPasswordInput: function (ev) {
        var password = ev.target.value;
        this._updatePasswordRequirements(password);
    },

    /**
     * Confirm password validation
     * @private
     */
    _onConfirmPasswordInput: function (ev) {
        var passwordInput = this.el.querySelector('input[name="password"]');
        var confirmPassword = ev.target.value;
        var password = passwordInput ? passwordInput.value : '';
        
        if (confirmPassword && password !== confirmPassword) {
            ev.target.classList.add('is-invalid');
        } else {
            ev.target.classList.remove('is-invalid');
        }
    },

    /**
     * Update password requirements visual feedback
     * @private
     */
    _updatePasswordRequirements: function (password) {
        var requirements = this.el.querySelectorAll('.requirement');
        
        requirements.forEach(function(req) {
            var type = req.getAttribute('data-requirement');
            var icon = req.querySelector('i');
            var isValid = false;
            
            switch(type) {
                case 'length':
                    isValid = password.length >= 8 && password.length <= 12;
                    break;
                case 'uppercase':
                    isValid = /[A-Z]/.test(password);
                    break;
                case 'number':
                    isValid = /[0-9]/.test(password);
                    break;
                case 'special':
                    isValid = /[!@#$%^&*(),.?":{}|<>]/.test(password);
                    break;
            }
            
            if (isValid) {
                icon.className = 'fa fa-check text-success';
                req.classList.add('valid');
            } else {
                icon.className = 'fa fa-times text-danger';
                req.classList.remove('valid');
            }
        });
    },

    /**
     * @private
     */
    _onSubmit: function (ev) {
        ev.preventDefault();
        var self = this;
        
        // validate password field
        var passwordInput = this.el.querySelector('input[name="password"]');
        var confirmPasswordInput = this.el.querySelector('input[name="confirm_password"]');
        if (passwordInput) {
            var password = passwordInput.value;
            var confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';
            
            // Password requirements validation
            var passwordErrors = [];
            
            // Length validation (8-12 characters)
            if (password.length < 8 || password.length > 12) {
                passwordErrors.push('La contraseña debe tener entre 8 y 12 caracteres');
            }
            
            // Uppercase letter validation
            if (!/[A-Z]/.test(password)) {
                passwordErrors.push('La contraseña debe contener al menos una letra mayúscula');
            }
            
            // Number validation
            if (!/[0-9]/.test(password)) {
                passwordErrors.push('La contraseña debe contener al menos un número');
            }
            
            // Special character validation
            if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
                passwordErrors.push('La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?":{}|<>)');
            }
            
            // Password confirmation validation
            if (confirmPassword && password !== confirmPassword) {
                passwordErrors.push('Las contraseñas no coinciden');
            }
            
            if (passwordErrors.length > 0) {
                this.$('.reset_password_error').remove();
                var errorMsg = '<ul class="mb-0">';
                passwordErrors.forEach(function(error) {
                    errorMsg += '<li>' + error + '</li>';
                });
                errorMsg += '</ul>';
                this.$el.prepend('<div class="alert alert-danger reset_password_error" role="alert">' + errorMsg + '</div>');
                passwordInput.focus();
                return false;
            }
        }
        
        var $btn = this.$('.oe_login_buttons > button[type="submit"]');
        $btn.attr('disabled', 'disabled');
        $btn.prepend('<i class="fa fa-refresh fa-spin"/> ');
        
        // Use AJAX to submit form and handle server errors
        var formData = new FormData(this.el);
        
        fetch(this.el.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(function(response) {
            console.log('Reset password response status:', response.status);
            return response.text();
        })
        .then(function(html) {
            console.log('Reset password response received, length:', html.length);
            
            // Parse the response to check for errors
            var parser = new DOMParser();
            var doc = parser.parseFromString(html, 'text/html');
            
            // Look for error in multiple places
            var errorElement = doc.querySelector('.alert-danger') || 
                             doc.querySelector('p[role="alert"]') ||
                             doc.querySelector('[class*="error"]');
            
            console.log('Error element found:', !!errorElement);
            
            if (errorElement) {
                // Server returned an error, display it
                console.log('Attempting to display error message');
                
                // Remove existing errors
                var existingErrors = self.el.querySelectorAll('.reset_password_error');
                existingErrors.forEach(function(err) { err.remove(); });
                
                var errorText = errorElement.textContent.trim();
                console.log('Error text:', errorText);
                
                if (errorText) {
                    // Show alert with error message
                    alert(errorText);
                    
                    // Create error div using vanilla JS for better compatibility
                    var errorDiv = document.createElement('div');
                    errorDiv.className = 'alert alert-danger reset_password_error';
                    errorDiv.setAttribute('role', 'alert');
                    errorDiv.textContent = errorText;
                    
                    // Insert at the beginning of the form
                    self.el.insertBefore(errorDiv, self.el.firstChild);
                    console.log('Error message inserted into DOM');
                    
                    // Re-enable button
                    $btn.removeAttr('disabled');
                    $btn.find('.fa-refresh').remove();
                    
                    // Scroll to error
                    setTimeout(function() {
                        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 100);
                } else {
                    console.warn('Error element found but no text content');
                    // Re-enable button
                    $btn.removeAttr('disabled');
                    $btn.find('.fa-refresh').remove();
                }
            } else {
                console.log('No error found, checking for success indicators');
                // Success - check for success message or redirect
                var successElement = doc.querySelector('.alert-success');
                if (successElement) {
                    // Password reset email sent successfully
                    window.location.reload();
                } else {
                    // Password was reset, redirect to login
                    window.location.href = '/web/login';
                }
            }
        })
        .catch(function(error) {
            console.error('Error submitting form:', error);
            // Re-enable button
            $btn.removeAttr('disabled');
            $btn.find('.fa-refresh').remove();
            
            // Remove existing errors
            var existingErrors = self.el.querySelectorAll('.reset_password_error');
            existingErrors.forEach(function(err) { err.remove(); });
            
            // Show generic error using vanilla JS
            var errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger reset_password_error';
            errorDiv.setAttribute('role', 'alert');
            errorDiv.textContent = 'Error al procesar el formulario. Por favor, intente nuevamente.';
            self.el.insertBefore(errorDiv, self.el.firstChild);
        });
    },
});
