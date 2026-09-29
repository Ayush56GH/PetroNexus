/**
 * PetroNexus Authentication Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  // Check if on login page
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      const errorAlert = document.getElementById('errorAlert');

      try {
        errorAlert.style.display = 'none';
        const res = await PetroNexusAPI.login(email, password);
        PetroNexusAPI.setToken(res.access_token);
        PetroNexusAPI.setUser(res.user);
        window.location.href = '/dashboard.html';
      } catch (err) {
        errorAlert.textContent = err.message || 'Login failed. Please verify credentials.';
        errorAlert.style.display = 'block';
      }
    });

    // Quick demo login fill helper
    const demoBtn = document.getElementById('fillDemoCredentials');
    if (demoBtn) {
      demoBtn.addEventListener('click', () => {
        document.getElementById('email').value = 'engineer@oilindia.in';
        document.getElementById('password').value = 'OilIndia@2026';
      });
    }
  }

  // Check if on register page
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errorAlert = document.getElementById('errorAlert');
      const fullName = document.getElementById('fullName').value.trim();
      const email = document.getElementById('email').value.trim();
      const employeeId = document.getElementById('employeeId').value.trim();
      const department = document.getElementById('department').value.trim();
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirmPassword').value;

      if (password !== confirmPassword) {
        errorAlert.textContent = 'Passwords do not match.';
        errorAlert.style.display = 'block';
        return;
      }

      try {
        errorAlert.style.display = 'none';
        await PetroNexusAPI.register({
          full_name: fullName,
          email,
          employee_id: employeeId,
          department,
          password,
          confirm_password: confirmPassword
        });
        alert('Registration successful! Please login with your credentials.');
        window.location.href = '/login.html';
      } catch (err) {
        errorAlert.textContent = err.message || 'Registration failed.';
        errorAlert.style.display = 'block';
      }
    });
  }

  // Populate user profile info in navbar if logged in
  const userDisplay = document.getElementById('currentUserDisplay');
  if (userDisplay) {
    const user = PetroNexusAPI.getUser();
    if (user && user.full_name) {
      userDisplay.textContent = `${user.full_name} (${user.role || 'DRILLING_ENGINEER'})`;
    } else {
      userDisplay.textContent = 'Rajesh Baruah (DRILLING_ENGINEER)';
    }
  }

  // Logout button handler
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      PetroNexusAPI.logout();
    });
  }
});
