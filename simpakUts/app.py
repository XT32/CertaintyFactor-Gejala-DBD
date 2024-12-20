from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# MySQL Database Configuration
db_config = {
    'host': '192.168.1.39',
    'port': '3307',
    'user': 'xt',
    'password': 'adminxt',
    'database': 'simpak'
}

def connect_db():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id_gejala, symptom_name FROM gejala")
    gejala_list = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', gejala_list=gejala_list)

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # Mengambil daftar gejala dari database untuk diakses nilainya
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id_gejala FROM gejala")
        gejala_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Ambil nilai CF user dari form untuk setiap gejala
        cf_user_values = []
        for gejala_id in gejala_ids:
            cf_user_value = request.form.get(f'cf_user[{gejala_id}]', 0)
            cf_user_values.append(float(cf_user_value))
        
        # Koneksi ke database untuk mengambil nilai CF expert
        conn = connect_db()
        cursor = conn.cursor()
        combined_cf_list = []
        
        for i, gejala_id in enumerate(gejala_ids):
            cursor.execute("SELECT cf_expert FROM certainty_factors WHERE id_gejala = %s", (gejala_id,))
            result = cursor.fetchone()
            if result:
                cf_expert = result[0]
                cf_user = cf_user_values[i]
                combined_cf = cf_expert * cf_user
                print(combined_cf)
                combined_cf_list.append(combined_cf)  # Simpan setiap hasil perkalian ke dalam daftar
        
        conn.close()
        
        # Lakukan perhitungan bertingkat pada combined_cf_list
        if combined_cf_list:
            # Inisialisasi `c_old` dengan combined_cf_list[0]
            c_old = combined_cf_list[0]
            
            # Menghitung nilai bertingkat untuk setiap index di `combined_cf_list`
            for cf in combined_cf_list[1:]:
                c_old = c_old + cf * (1 - c_old)
            
            # Hasil akhir diambil dari nilai terakhir `c_old` dan dikali 100%
            total_bobot = c_old * 100
        else:
            total_bobot = 0  # Default jika tidak ada gejala yang dipilih atau dihitung

        # Narasi berdasarkan total_bobot
        if total_bobot < 30:
            narrative = "Kemungkinan Anda tidak terkena DBD. Namun, tetap waspada terhadap gejala yang muncul."
        elif 30 <= total_bobot < 70:
            narrative = "Ada kemungkinan Anda terkena DBD. Sebaiknya konsultasikan dengan dokter jika gejala berlanjut."
        else:
            narrative = "Tinggi kemungkinan Anda terkena DBD. Segera periksakan diri ke dokter untuk mendapatkan penanganan yang tepat."

        return render_template('result.html', total_bobot=total_bobot, narrative=narrative)

if __name__ == '__main__':
    app.run(debug=True)
