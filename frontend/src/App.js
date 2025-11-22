import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

const API = process.env.REACT_APP_API_URL || "http://127.0.0.1:5000";

/* ================================================================================
   LOGIN COMPONENT — Handles user credentials and authentication flow.
================================================================================ */
function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  // Sends login data to backend and validates user identity
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      // Backend controls the success state — relay message to UI
      if (!res.ok || !data.success) {
        setError(data.message || "Login failed");
        return;
      }

      // Pass authenticated user back to App component
      onLogin(data.user);
    } catch (err) {
      console.error("Login error:", err);
      setError("Network error — backend may be offline.");
    }
  };

  return (
    <div style={{
      maxWidth: 400,
      margin: "50px auto",
      padding: 20,
      borderRadius: 10,
      border: "1px solid #ccc",
      fontFamily: "Arial, sans-serif",
    }}>

      <h2>Hospital System Login</h2>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 10 }}>
          <label>Username</label><br />
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{ width: "100%", padding: 6 }}
            required
          />
        </div>

        <div style={{ marginBottom: 10 }}>
          <label>Password</label><br />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%", padding: 6 }}
            required
          />
        </div>

        {/* Display errors coming from login validation */}
        {error && <div style={{ color: "red", marginBottom: 10 }}>{error}</div>}

        <button type="submit" style={{ padding: "6px 12px" }}>
          Login
        </button>
      </form>
    </div>
  );
}

/* ================================================================================
   PATIENT PAGE — Displays all patients retrieved from the backend.
================================================================================ */
function PatientsPage({ patients }) {
  return (
    <div>
      <h2>Patients</h2>

      {/* Table presenting patient demographic details */}
      <table border="1" cellPadding="6" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th>ID</th><th>Name</th><th>DOB</th><th>Gender</th><th>Address</th><th>Phone</th>
          </tr>
        </thead>

        <tbody>
          {patients.map((p) => (
            <tr key={p.patient_id}>
              <td>{p.patient_id}</td>
              <td>{p.name}</td>
              <td>{p.date_of_birth}</td>
              <td>{p.gender}</td>
              <td>{p.address}</td>
              <td>{p.phone}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ================================================================================
   DOCTORS PAGE — Pulls and shows all registered doctors from backend.
================================================================================ */
function DoctorsPage() {
  const [doctors, setDoctors] = useState([]);

  // Loads doctors only once when page is opened
  useEffect(() => {
    fetch(`${API}/doctors`)
      .then((res) => res.json())
      .then((data) => setDoctors(data));
  }, []);

  return (
    <div>
      <h2>Doctors</h2>

      {/* Table includes doctor specialties and contact info */}
      <table border="1" cellPadding="6" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th>ID</th><th>Name</th><th>Specialty</th><th>Phone</th><th>Email</th>
          </tr>
        </thead>

        <tbody>
          {doctors.map((d) => (
            <tr key={d.doctor_id}>
              <td>{d.doctor_id}</td>
              <td>{d.name}</td>
              <td>{d.specialty}</td>
              <td>{d.phone}</td>
              <td>{d.email}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ================================================================================
   APPOINTMENTS PAGE — Supports full CRUD operations for appointments.
================================================================================ */
function AppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);

  const [formMode, setFormMode] = useState("add");
  const [formData, setFormData] = useState({
    appointment_id: null,
    patient_id: "",
    doctor_id: "",
    appointment_date: "",
    reason: "",
  });

  // Fetches all appointment records from backend
  const loadAppointments = () => {
    fetch(`${API}/appointments`)
      .then((res) => res.json())
      .then((data) => setAppointments(data));
  };

  // Loads dropdown list of patients
  const loadPatients = () => {
    fetch(`${API}/patients`)
      .then((res) => res.json())
      .then((data) => setPatients(data));
  };

  // Loads dropdown list of doctors
  const loadDoctors = () => {
    fetch(`${API}/doctors`)
      .then((res) => res.json())
      .then((data) => setDoctors(data));
  };

  // Fetch initial data needed for CRUD operations
  useEffect(() => {
    loadAppointments();
    loadPatients();
    loadDoctors();
  }, []);

  // Updates internal form data when inputs change
  const updateField = (key, value) => {
    setFormData((old) => ({ ...old, [key]: value }));
  };

  // Creates a new appointment OR updates an existing one
  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      patient_id: formData.patient_id,
      doctor_id: formData.doctor_id,
      appointment_date: formData.appointment_date,
      reason: formData.reason,
    };

    let url = `${API}/appointments`;
    let method = "POST";

    if (formMode === "edit") {
      url = `${API}/appointments/${formData.appointment_id}`;
      method = "PUT";
    }

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await res.json();

    // Refresh data and clear form after a successful update/add
    if (result.success) {
      alert(formMode === "add" ? "Appointment Added" : "Appointment Updated");

      setFormData({
        appointment_id: null,
        patient_id: "",
        doctor_id: "",
        appointment_date: "",
        reason: "",
      });

      setFormMode("add");
      loadAppointments();
    } else {
      alert(result.message || "Error occurred while submitting");
    }
  };

  // Deletes a chosen appointment after user confirmation
  const deleteAppointment = async (id) => {
    if (!window.confirm("Delete this appointment?")) return;

    const res = await fetch(`${API}/appointments/${id}`, { method: "DELETE" });
    const data = await res.json();

    if (data.success) {
      loadAppointments();
    } else {
      alert(data.message);
    }
  };

  // Places appointment info back into form so it can be edited
  const editAppointment = (appt) => {
    setFormMode("edit");
    setFormData({
      appointment_id: appt.appointment_id,
      patient_id: appt.patient_id,
      doctor_id: appt.doctor_id,
      appointment_date: appt.appointment_date.replace(" ", "T"),
      reason: appt.reason,
    });
  };

  return (
    <div>
      <h2>Appointments (CRUD)</h2>

      {/* ------------------------------------
            FORM UI FOR ADDING AND EDITING
      ------------------------------------ */}
      <form
        onSubmit={handleSubmit}
        style={{
          marginBottom: 30,
          padding: 15,
          border: "1px solid #aaa",
          borderRadius: 8,
        }}
      >
        <h3>{formMode === "add" ? "Add New Appointment" : "Edit Appointment"}</h3>

        <label>Patient:</label><br />
        <select
          value={formData.patient_id}
          onChange={(e) => updateField("patient_id", e.target.value)}
          required
        >
          <option value="">Select patient</option>
          {patients.map((p) => (
            <option key={p.patient_id} value={p.patient_id}>
              {p.name}
            </option>
          ))}
        </select>

        <br /><br />

        <label>Doctor:</label><br />
        <select
          value={formData.doctor_id}
          onChange={(e) => updateField("doctor_id", e.target.value)}
          required
        >
          <option value="">Select doctor</option>
          {doctors.map((d) => (
            <option key={d.doctor_id} value={d.doctor_id}>
              {d.name} ({d.specialty})
            </option>
          ))}
        </select>

        <br /><br />

        <label>Date & Time:</label><br />
        <input
          type="datetime-local"
          value={formData.appointment_date}
          onChange={(e) => updateField("appointment_date", e.target.value)}
          required
        />

        <br /><br />

        <label>Reason:</label><br />
        <input
          type="text"
          value={formData.reason}
          onChange={(e) => updateField("reason", e.target.value)}
          required
        />

        <br /><br />

        <button type="submit" style={{ padding: "6px 12px" }}>
          {formMode === "add" ? "Add Appointment" : "Save Changes"}
        </button>
      </form>

      {/* ------------------------------------
            APPOINTMENTS LIST TABLE
      ------------------------------------ */}
      <table border="1" cellPadding="6" style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>ID</th><th>Date</th><th>Reason</th><th>Patient</th><th>Doctor</th><th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {appointments.map((a) => (
            <tr key={a.appointment_id}>
              <td>{a.appointment_id}</td>
              <td>{a.appointment_date}</td>
              <td>{a.reason}</td>
              <td>{a.patient_name}</td>
              <td>{a.doctor_name}</td>

              <td>
                <button onClick={() => editAppointment(a)}>Edit</button>
                <button
                  onClick={() => deleteAppointment(a.appointment_id)}
                  style={{ marginLeft: 8, color: "red" }}
                >
                  Delete
                </button>
              </td>

            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ================================================================================
   DASHBOARD PAGE — Fetches stats and displays a bar chart overview.
================================================================================ */
function DashboardPage() {
  const [stats, setStats] = useState(null);

  // Load statistics from backend as soon as dashboard loads
  useEffect(() => {
    fetch(`${API}/stats`)
      .then((res) => res.json())
      .then((data) => setStats(data));
  }, []);

  if (!stats) {
    return (
      <div>
        <h2>Dashboard</h2>
        <p>Loading stats...</p>
      </div>
    );
  }

  // Convert stats into a format readable by Recharts
  const chartData = [
    { name: "Patients", value: stats.patients },
    { name: "Doctors", value: stats.doctors },
    { name: "Appointments", value: stats.appointments },
    { name: "Treatments", value: stats.treatments },
    { name: "Billing", value: stats.billing },
    { name: "Users", value: stats.users },
  ];

  return (
    <div>
      <h2>Dashboard</h2>

      {/* Bar chart visualizing database counts */}
      <div style={{ marginTop: 20 }}>
        <h3>System Statistics</h3>

        <BarChart width={600} height={300} data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="value" fill="#8884d8" />
        </BarChart>
      </div>
    </div>
  );
}

/* ================================================================================
   MAIN APPLICATION — Controls navigation and access to all pages.
================================================================================ */
function App() {
  const [user, setUser] = useState(null);
  const [patients, setPatients] = useState([]);
  const [page, setPage] = useState("dashboard");

  // Load patients once user logs in
  useEffect(() => {
    if (!user) return;

    fetch(`${API}/patients`)
      .then((res) => res.json())
      .then((data) => setPatients(data));
  }, [user]);

  // Clears session data when user logs out
  const handleLogout = () => {
    setUser(null);
    setPatients([]);
    setPage("dashboard");
  };

  // If user is not logged in, only show login screen
  if (!user) return <Login onLogin={setUser} />;

  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif" }}>

      {/* Header area with logout option */}
      <header style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
        <h1>Hospital Management System</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>

      {/* Simple navigation bar for switching between pages */}
      <nav style={{ marginBottom: 20 }}>
        <button onClick={() => setPage("dashboard")}>Dashboard</button>
        <button onClick={() => setPage("patients")}>Patients</button>
        <button onClick={() => setPage("doctors")}>Doctors</button>
        <button onClick={() => setPage("appointments")}>Appointments</button>
      </nav>

      {/* Responsible for displaying the selected page */}
      {page === "dashboard" && <DashboardPage />}
      {page === "patients" && <PatientsPage patients={patients} />}
      {page === "doctors" && <DoctorsPage />}
      {page === "appointments" && <AppointmentsPage />}
    </div>
  );
}

export default App;
