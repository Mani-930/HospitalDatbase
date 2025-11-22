from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc
import bcrypt

app = Flask(__name__)
CORS(app)  # Allows the React frontend to communicate with this API

# ================================================================================
#  DATABASE CONNECTION HELPER
#  Creates a connection to the SQL Server database whenever needed.
# ================================================================================
def get_conn():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=MANI\\SQLEXPRESS;"  
        "DATABASE=HospitalMgmtDB;"
        "Trusted_Connection=yes;"
    )

# ================================================================================
#  DEBUG ENDPOINT — Lists all registered Flask routes
# ================================================================================
@app.route("/__routes", methods=["GET"])
def list_routes():
    """Returns all API routes so developers can inspect the active endpoints."""
    return jsonify([str(r) for r in app.url_map.iter_rules()])

# ================================================================================
#  SYSTEM STATISTICS — Counts records from each major table
# ================================================================================
@app.route("/stats", methods=["GET"])
def get_stats():
    try:
        conn = get_conn()
        cur = conn.cursor()

        def count(sql):
            cur.execute(sql)
            return cur.fetchone()[0]

        stats = {
            "patients":     count("SELECT COUNT(*) FROM dbo.Patient"),
            "doctors":      count("SELECT COUNT(*) FROM dbo.Doctor"),
            "appointments": count("SELECT COUNT(*) FROM dbo.Appointment"),
            "treatments":   count("SELECT COUNT(*) FROM dbo.Treatment"),
            "billing":      count("SELECT COUNT(*) FROM dbo.Billing"),
            "users":        count("SELECT COUNT(*) FROM dbo.AppUser"),
        }
        conn.close()
        return jsonify(stats)

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500

# ================================================================================
#  LOGIN ENDPOINT — Validates user credentials using bcrypt hashing
# ================================================================================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, password_hash, full_name, role
            FROM dbo.AppUser
            WHERE username = ?
        """, (username,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"success": False, "message": "User not found"}), 401

        db_username, stored_hash, full_name, role = row

        # Convert hash from SQL NVARCHAR to bytes for bcrypt
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": {
                    "username": db_username,
                    "full_name": full_name,
                    "role": role
                }
            })
        else:
            return jsonify({"success": False, "message": "Invalid password"}), 401

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500

# ================================================================================
#  PATIENT LIST — Returns all patient records
# ================================================================================
@app.route("/patients", methods=["GET"])
def get_patients():
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT patient_id, name, date_of_birth, gender, address, phone
            FROM dbo.Patient
            ORDER BY patient_id
        """)
        rows = cursor.fetchall()
        conn.close()

        return jsonify([
            {
                "patient_id": r[0],
                "name": r[1],
                "date_of_birth": str(r[2]) if r[2] else None,
                "gender": r[3],
                "address": r[4],
                "phone": r[5]
            } for r in rows
        ])

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500

# ================================================================================
#  DOCTOR LIST — Retrieves all doctors from the database
# ================================================================================
@app.route("/doctors", methods=["GET"])
def get_doctors():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT doctor_id, name, specialty, phone, email
            FROM dbo.Doctor
            ORDER BY name
        """)
        rows = cur.fetchall()
        conn.close()

        return jsonify([
            {
                "doctor_id": r[0],
                "name": r[1],
                "specialty": r[2],
                "phone": r[3],
                "email": r[4]
            } for r in rows
        ])

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500

# ================================================================================
#  APPOINTMENT LIST — Supports optional filtering by patient, doctor, or date
# ================================================================================
@app.route("/appointments", methods=["GET"])
def get_appointments():
    """
    Optional URL filters:
        ?patient_id=1
        ?doctor_id=2
        ?from=2025-01-01
        ?to=2025-01-31
    """
    try:
        patient_id = request.args.get("patient_id")
        doctor_id  = request.args.get("doctor_id")
        dt_from    = request.args.get("from")
        dt_to      = request.args.get("to")

        where = []
        params = []

        if patient_id:
            where.append("a.patient_id = ?")
            params.append(int(patient_id))

        if doctor_id:
            where.append("a.doctor_id = ?")
            params.append(int(doctor_id))

        if dt_from:
            where.append("a.appointment_date >= ?")
            params.append(dt_from)

        if dt_to:
            where.append("a.appointment_date <= ?")
            params.append(dt_to)

        sql = """
            SELECT a.appointment_id, a.appointment_date, a.reason,
                   p.patient_id, p.name AS patient_name,
                   d.doctor_id, d.name AS doctor_name
            FROM dbo.Appointment a
            JOIN dbo.Patient p ON p.patient_id = a.patient_id
            JOIN dbo.Doctor d  ON d.doctor_id = a.doctor_id
        """

        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY a.appointment_date DESC, a.appointment_id DESC"

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        return jsonify([
            {
                "appointment_id": r[0],
                "appointment_date": str(r[1]),
                "reason": r[2],
                "patient_id": r[3],
                "patient_name": r[4],
                "doctor_id": r[5],
                "doctor_name": r[6]
            } for r in rows
        ])

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500

# ================================================================================
#  TREATMENT LIST — Can filter results by appointment ID
# ================================================================================
@app.route("/treatments", methods=["GET"])
def get_treatments():
    try:
        appointment_id = request.args.get("appointment_id")
        where = ""
        params = []

        if appointment_id:
            where = "WHERE t.appointment_id = ?"
            params = [int(appointment_id)]

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT t.treatment_id, t.appointment_id,
                   t.diagnosis, t.prescription, t.notes
            FROM dbo.Treatment t
            {where}
            ORDER BY t.treatment_id DESC
        """, params)
        rows = cur.fetchall()
        conn.close()

        return jsonify([
            {
                "treatment_id": r[0],
                "appointment_id": r[1],
                "diagnosis": r[2],
                "prescription": r[3],
                "notes": r[4]
            } for r in rows
        ])

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500

# ================================================================================
#  BILLING LIST — Supports filtering by patient or payment status
# ================================================================================
@app.route("/billing", methods=["GET"])
def get_billing():
    try:
        patient_id = request.args.get("patient_id")
        status     = request.args.get("status")

        where = []
        params = []

        if patient_id:
            where.append("b.patient_id = ?")
            params.append(int(patient_id))

        if status:
            where.append("b.payment_status = ?")
            params.append(status)

        sql = """
            SELECT b.bill_id, b.patient_id, p.name AS patient_name,
                   b.treatment_id, b.amount, b.payment_status, b.billing_date
            FROM dbo.Billing b
            JOIN dbo.Patient p ON p.patient_id = b.patient_id
        """

        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY b.billing_date DESC, b.bill_id DESC"

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        return jsonify([
            {
                "bill_id": r[0],
                "patient_id": r[1],
                "patient_name": r[2],
                "treatment_id": r[3],
                "amount": float(r[4]) if r[4] is not None else None,
                "payment_status": r[5],
                "billing_date": str(r[6])
            } for r in rows
        ])

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500

# ================================================================================
# SERVER STARTUP
# ================================================================================
if __name__ == "__main__":
    print("Starting Flask from:", __file__)
    app.run(debug=True)

# ================================================================================
# INTERNAL HELPER — Converts an appointment DB row into JSON
# ================================================================================
def _appointment_row_to_json(r):
    return {
        "appointment_id": r[0],
        "appointment_date": str(r[1]),
        "reason": r[2],
        "patient_id": r[3],
        "patient_name": r[4],
        "doctor_id": r[5],
        "doctor_name": r[6]
    }

# ================================================================================
# CREATE APPOINTMENT
# ================================================================================
@app.route("/appointments", methods=["POST"])
def create_appointment():
    """
    Expected JSON example:
    {
      "patient_id": 1,
      "doctor_id": 2,
      "appointment_date": "2025-11-28 09:30:00",
      "reason": "Check-up"
    }
    """
    try:
        data = request.get_json()
        patient_id = int(data.get("patient_id"))
        doctor_id = int(data.get("doctor_id"))
        appointment_date = data.get("appointment_date")
        reason = data.get("reason")

        conn = get_conn()
        cur = conn.cursor()

        # Validate foreign keys
        cur.execute("SELECT COUNT(*) FROM dbo.Patient WHERE patient_id = ?", (patient_id,))
        if cur.fetchone()[0] == 0:
            conn.close()
            return jsonify({"success": False, "message": "Invalid patient_id"}), 400

        cur.execute("SELECT COUNT(*) FROM dbo.Doctor WHERE doctor_id = ?", (doctor_id,))
        if cur.fetchone()[0] == 0:
            conn.close()
            return jsonify({"success": False, "message": "Invalid doctor_id"}), 400

        # Insert new appointment
        cur.execute("""
            INSERT INTO dbo.Appointment (patient_id, doctor_id, appointment_date, reason)
            VALUES (?, ?, ?, ?)
        """, (patient_id, doctor_id, appointment_date, reason))

        cur.execute("SELECT SCOPE_IDENTITY()")
        new_id = int(cur.fetchone()[0])
        conn.commit()

        # Return created appointment (with joined doctor/patient names)
        cur.execute("""
            SELECT a.appointment_id, a.appointment_date, a.reason,
                   p.patient_id, p.name, d.doctor_id, d.name
            FROM dbo.Appointment a
            JOIN dbo.Patient p ON p.patient_id = a.patient_id
            JOIN dbo.Doctor d ON d.doctor_id = a.doctor_id
            WHERE a.appointment_id = ?
        """, (new_id,))
        row = cur.fetchone()
        conn.close()

        return jsonify({"success": True, "appointment": _appointment_row_to_json(row)}), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500

# ================================================================================
# UPDATE APPOINTMENT
# ================================================================================
@app.route("/appointments/<int:appointment_id>", methods=["PUT"])
def update_appointment(appointment_id):
    """
    Accepts partial or full updates for an appointment.
    Only supplied fields will be changed.
    """
    try:
        data = request.get_json()
        patient_id = data.get("patient_id")
        doctor_id = data.get("doctor_id")
        appointment_date = data.get("appointment_date")
        reason = data.get("reason")

        sets = []
        params = []

        if patient_id is not None:
            sets.append("patient_id = ?")
            params.append(int(patient_id))

        if doctor_id is not None:
            sets.append("doctor_id = ?")
            params.append(int(doctor_id))

        if appointment_date is not None:
            sets.append("appointment_date = ?")
            params.append(appointment_date)

        if reason is not None:
            sets.append("reason = ?")
            params.append(reason)

        if not sets:
            return jsonify({"success": False, "message": "Nothing to update"}), 400

        conn = get_conn()
        cur = conn.cursor()

        # Ensure the record exists
        cur.execute("SELECT COUNT(*) FROM dbo.Appointment WHERE appointment_id = ?", (appointment_id,))
        if cur.fetchone()[0] == 0:
            conn.close()
            return jsonify({"success": False, "message": "Appointment not found"}), 404

        # Validate FK references (if changed)
        if patient_id is not None:
            cur.execute("SELECT COUNT(*) FROM dbo.Patient WHERE patient_id = ?", (patient_id,))
            if cur.fetchone()[0] == 0:
                conn.close()
                return jsonify({"success": False, "message": "Invalid patient_id"}), 400

        if doctor_id is not None:
            cur.execute("SELECT COUNT(*) FROM dbo.Doctor WHERE doctor_id = ?", (doctor_id,))
            if cur.fetchone()[0] == 0:
                conn.close()
                return jsonify({"success": False, "message": "Invalid doctor_id"}), 400

        sql = f"UPDATE dbo.Appointment SET {', '.join(sets)} WHERE appointment_id = ?"
        params.append(appointment_id)

        cur.execute(sql, params)
        conn.commit()

        # Return updated record
        cur.execute("""
            SELECT a.appointment_id, a.appointment_date, a.reason,
                   p.patient_id, p.name, d.doctor_id, d.name
            FROM dbo.Appointment a
            JOIN dbo.Patient p ON p.patient_id = a.patient_id
            JOIN dbo.Doctor d ON d.doctor_id = a.doctor_id
            WHERE a.appointment_id = ?
        """, (appointment_id,))
        row = cur.fetchone()
        conn.close()

        return jsonify({"success": True, "appointment": _appointment_row_to_json(row)})

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500

# ================================================================================
# DELETE APPOINTMENT
# ================================================================================
@app.route("/appointments/<int:appointment_id>", methods=["DELETE"])
def delete_appointment(appointment_id):
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM dbo.Appointment WHERE appointment_id = ?", (appointment_id,))
        if cur.fetchone()[0] == 0:
            conn.close()
            return jsonify({"success": False, "message": "Appointment not found"}), 404

        cur.execute("DELETE FROM dbo.Appointment WHERE appointment_id = ?", (appointment_id,))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Appointment deleted"})

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {e}"}), 500
