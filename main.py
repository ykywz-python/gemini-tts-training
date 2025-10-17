from google import genai
from google.genai import types
from google.genai.errors import APIError
import wave
import time
import logging
import os
import glob

# Konfigurasi Logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    # Menentukan format waktu (time format) agar hanya menampilkan Jam:Menit:Detik (H:M:S)
    datefmt='%H:%M:%S' 
)

# --- PENGATURAN PATH FFMPEG MANUAL ---
# ⚠️ GANTI PATH BERIKUT DENGAN LOKASI FFmpeg YANG SEBENARNYA DI KOMPUTER ANDA
FFMPEG_EXECUTABLE_PATH = r"ffmpeg.exe" 
# Jika Anda menggunakan Linux/macOS, path mungkin seperti: r"/usr/local/bin/ffmpeg"

# Atur variabel lingkungan agar pydub dapat menemukan FFmpeg
try:
    if os.path.exists(FFMPEG_EXECUTABLE_PATH):
        os.environ["FFMPEG_PATH"] = FFMPEG_EXECUTABLE_PATH
        # Tambahkan folder bin-nya ke PATH agar pydub menemukannya dengan mudah
        os.environ["PATH"] += os.pathsep + os.path.dirname(FFMPEG_EXECUTABLE_PATH)
        logging.info("✅ Path FFmpeg berhasil diatur secara manual.")
    else:
        logging.warning(f"⚠️ FFmpeg tidak ditemukan di path yang ditentukan: {FFMPEG_EXECUTABLE_PATH}")
        logging.warning("Pydub mungkin gagal jika FFmpeg tidak ada di PATH sistem.")

except Exception as e:
    logging.error(f"❌ Gagal mengatur variabel lingkungan FFmpeg: {e}")

from pydub import AudioSegment

# --- Konfigurasi Global dan API Key Management ---
# Variabel Global untuk Rotasi Key
# Asumsi: API keys dimuat dari file 'api-keys.txt' (satu key per baris)
API_KEYS_LIST = []
current_api_key_index = 0

def load_api_keys(filepath='api-keys.txt'):
    """Memuat daftar API Key dari file teks."""
    global API_KEYS_LIST
    try:
        with open(filepath, 'r') as f:
            # Membaca semua baris dan menghilangkan spasi/newline
            keys = [line.strip() for line in f if line.strip()]
            if not keys:
                raise ValueError("File 'api-keys.txt' kosong atau tidak berisi key.")
            API_KEYS_LIST = keys
            logger.info(f"Ditemukan {len(API_KEYS_LIST)} API Key.")
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{filepath}' tidak ditemukan. Buat file dan isi key di dalamnya.")

def get_current_api_key():
    """Mengembalikan API Key yang saat ini digunakan."""
    if not API_KEYS_LIST:
        return None
    # Pastikan indeks berada dalam batas
    index = current_api_key_index % len(API_KEYS_LIST)
    return API_KEYS_LIST[index]

def rotate_api_key():
    """Memutar indeks ke API Key berikutnya."""
    global current_api_key_index
    current_api_key_index = (current_api_key_index + 1) % len(API_KEYS_LIST)
    logger.warning(f"API Key diputar. Index berikutnya: {current_api_key_index}")

# --- Fungsi Utility WAV (Diperbarui) ---
def save_audio_to_wav(filename: str, pcm_data: bytes, chunk_index: int):
    """Menulis data PCM audio biner ke file WAV dengan indeks chunk."""
    # Menghasilkan nama file yang unik, misal: 'out_rotated_01.wav'
    final_filename = f"{os.path.splitext(filename)[0]}_{chunk_index:02d}.wav"
    
    # ... (sisa implementasi wave.open tetap sama)
    try:
        with wave.open(final_filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)
        logger.info(f"✅ File audio berhasil disimpan ke: {final_filename}")
    except Exception as e:
        logger.error(f"❌ Error saat menyimpan file WAV: {e}")

# --- Fungsi Pembagi Teks ---
def split_text_into_chunks_by_chars(full_text: str, max_chars_per_chunk: int) -> list[str]:
    """
    Membagi teks menjadi chunk berdasarkan batas karakter yang diterima sebagai argumen, 
    berusaha memecah pada akhir kalimat.
    """
    
    # Menghilangkan spasi berlebihan dan mempersingkat teks
    clean_text = ' '.join(full_text.split())
    
    chunks = []
    current_start = 0
    total_length = len(clean_text)

    while current_start < total_length:
        remaining_length = total_length - current_start
        
        # Jika sisa teks kurang dari batas maksimum, ambil semuanya
        if remaining_length <= max_chars_per_chunk:
            chunk = clean_text[current_start:]
            chunks.append(chunk)
            break
            
        # Tentukan titik potong maksimum
        max_end = current_start + max_chars_per_chunk
        
        # Cari titik potong yang 'bersih' (akhir kalimat: '.', '!', '?')
        split_point = -1
        
        # Cari tanda titik/tanya/seru dalam 200 karakter terakhir sebelum batas
        search_area_start = max_end - 200
        if search_area_start < current_start:
             search_area_start = current_start

        match = re.search(r'[.?!]\s', clean_text[search_area_start:max_end], re.DOTALL | re.IGNORECASE)
        
        if match:
            # Hitung posisi absolut titik potong
            relative_index = match.end()
            split_point = search_area_start + relative_index
        
        # Jika tidak ditemukan titik potong yang bagus, potong saja pada batas maksimum
        if split_point == -1 or split_point <= current_start:
            split_point = max_end
            
        chunk = clean_text[current_start:split_point].strip()
        chunks.append(chunk)
        
        # Update posisi awal untuk chunk berikutnya
        current_start = split_point
        
    logger.info(f"Teks dibagi menjadi {len(chunks)} chunk (Max {max_chars_per_chunk} karakter/chunk) untuk menghemat RPD.")
    return chunks

# --- Fungsi Iterasi Utama ---
def generate_audio_for_chunks(
    full_prompt: str, 
    voice: str, 
    base_filename: str, 
    max_chars_per_chunk: int,
    max_retries: int,          # ARGUMEN BARU
    base_delay: int,           # ARGUMEN BARU
    temperature: float = 0.7
):
    """
    Memecah teks menjadi chunk dan menghasilkan audio untuk setiap chunk 
    dengan mekanisme rotasi API key.
    """
    
    # 1. Membagi Teks
    text_chunks = split_text_into_chunks_by_chars(full_prompt, max_chars_per_chunk)
    
    total_chunks = len(text_chunks)
    
    # 2. Iterasi dan Generasi Audio
    for i, chunk in enumerate(text_chunks):
        logger.info(f"\n--- Memproses Chunk {i + 1} dari {total_chunks} ---")
        
        # Panggil fungsi TTS dengan retry dan rotasi
        make_tts_request_with_retry(
            prompt=chunk, 
            voice=voice, 
            base_filename=base_filename,
            chunk_index=i + 1,
            max_retries=max_retries,     # DITERUSKAN
            base_delay=base_delay,       # DITERUSKAN
            temperature=temperature
        )        
        
        # Opsional: Jeda singkat antar permintaan untuk menghindari rate-limit
        time.sleep(0.5)

# --- Fungsi Utama dengan Rotasi Key ---
def make_tts_request_with_retry(
    prompt: str, 
    voice: str, 
    base_filename: str, 
    chunk_index: int, 
    max_retries: int,          # ARGUMEN BARU
    base_delay: int,           # ARGUMEN BARU
    temperature: float = 0.7
):
    """
    Melakukan permintaan TTS dengan mekanisme retry dan rotasi API key
    jika terjadi ResourceExhaustedError (Kuota Habis).
    """
    
    max_retries = len(API_KEYS_LIST)
    if max_retries == 0:
        raise ValueError('Tidak ada API Key yang tersedia untuk digunakan.')

    for attempt in range(max_retries):
        api_key = get_current_api_key()
        
        if not api_key:
            logger.error("API Key saat ini tidak valid atau kosong.")
            if attempt + 1 < max_retries:
                rotate_api_key()
                continue
            else:
                raise ValueError('Semua API Key tidak valid.')

        try:
            logger.info(f'Mencoba request ke Gemini dengan API Key index: {current_api_key_index} key: {api_key} (Percobaan {attempt + 1}/{max_retries})')
            
            # Inisialisasi Klien Gemini
            client = genai.Client(api_key=api_key)
            
            # Konfigurasi Permintaan
            config = types.GenerateContentConfig(
                temperature=temperature,    
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice,
                        )
                    )
                ),
            )
            
            # Panggilan API
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=config
            )

            
            try:
                data = response.candidates[0].content.parts[0].inline_data.data
            except (AttributeError, IndexError) as e:
                # Jika pengambilan data gagal, kita putar key dan coba lagi
                logger.error(f'❌ Gagal mengambil data audio. Rotasi key. Error: {e}')
                raise Exception("Gagal parsing respons audio.") # Lempar error API untuk memicu rotasi
                
            # Menyimpan File
            save_audio_to_wav(base_filename, data, chunk_index)
            return 

        except APIError as e:
            if "RESOURCE_EXHAUSTED" in str(e) or attempt == max_retries - 1:
                # Jika kuota habis ATAU ini adalah upaya terakhir, ROTASI KEY
                rotate_api_key()
                logger.warning(f"⚠️ Kuota habis atau Gagal setelah {max_retries} upaya. Mencoba key baru...")
                
                # Jika kuota habis, loop akan berlanjut ke upaya berikutnya dengan key baru
                # Jika ini adalah upaya terakhir, dan rotate_api_key tidak melempar error,
                # maka loop akan keluar dan mencapai gagal total di bawah.
                
            else:
                # Jika error sementara (bukan kuota), coba lagi dengan penundaan eksponensial
                delay = base_delay * (2 ** attempt) 
                logger.warning(f"⚠️ Error sementara ({e}). Mencoba lagi dalam {delay:.1f} detik.")
                time.sleep(delay)
                
        except Exception as e:
            # Error non-API (misal: error I/O file, error parsing response)
            logger.error(f'❌ Error tak terduga: {e}')
            raise e

# --- Fungsi Penggabungan Audio ---
def combine_audio_chunks(base_filename: str, output_filename: str = 'final_narasi.wav', delete_chunks: bool = True):

    """
    Menggabungkan semua file chunk audio (*_01.wav, *_02.wav, dst.) menjadi satu file.
    
    Args:
        base_filename: Nama dasar file yang dihasilkan (misal: 'narasi_tts').
        output_filename: Nama file output tunggal (misal: 'final_narasi.wav').
    """
    
    # Mencari semua file yang cocok dengan pola (contoh: narasi_tts_01.wav, narasi_tts_02.wav)
    search_pattern = f"{base_filename}_*.wav"
    file_list = sorted(glob.glob(search_pattern))
    
    if not file_list:
        logger.error(f"❌ Tidak ditemukan file WAV yang cocok dengan pola '{search_pattern}'.")
        return

    logger.info(f"Ditemukan {len(file_list)} file untuk digabungkan.")
    
    combined_audio = AudioSegment.empty()
    
    try:
        for file_path in file_list:
            logger.info(f"⏳ Menggabungkan: {file_path}")
            # Memuat file WAV ke objek AudioSegment
            chunk_audio = AudioSegment.from_wav(file_path)
            # Menambahkan chunk ke audio gabungan
            combined_audio += chunk_audio
                
        # Mengekspor audio gabungan ke file WAV baru
        combined_audio.export(output_filename, format="wav")

        if delete_chunks:
            # Hapus file chunk setelah gabungan berhasil
            for file_path in file_list:
                os.remove(file_path)
                logger.debug(f"🗑️ File chunk sementara dihapus: {file_path}")
        
        logger.info(f"✅ Penggabungan Selesai! File disimpan sebagai: {output_filename}")
        
    except FileNotFoundError:
        # Ini biasanya terjadi jika FFmpeg tidak ditemukan
        logger.error("❌ Error: FFmpeg tidak ditemukan!")
        logger.error("Pastikan FFmpeg terinstal dan PATH sistem telah dikonfigurasi dengan benar.")
    except Exception as e:
        logger.error(f"❌ Terjadi error saat memproses audio: {e}")

# --- Eksekusi Script ---
if __name__ == "__main__":
    # ... (load_api_keys) ...
    
    FULL_TEXT_PROMPT = """
START_SCRIPT

[INSTRUKSI_SUARA: Bicara dengan energik dan punchy. Seperti ngobrol santai dengan teman. Cepat tapi jelas. Seperti kakak yang excited cerita ke adik.]

[TEKS_SCRIPT]
Ini dia 5 fakta unik yang bikin kamu melongo dari Korea Selatan!

[JEDA: 0.2 detik]

[INSTRUKSI_SUARA: Semangat, persuasif, hangat]
[TEKS_SCRIPT]
Like dan subscribe, biar kamu jadi anak cerdas, oke!

[JEDA: 0.2 detik]

[INSTRUKSI_SUARA: Jelas dan to the point]
[TEKS_SCRIPT]
Langsung kita mulai.

[JEDA: 0.2 detik]

[INSTRUKSI_SUARA: Casual, mengundang, ceria]
[TEKS_SCRIPT]
Pertama. Umur di sana beda. Saat lahir, kamu sudah dianggap setahun. Loh, kok sudah setahun?

[JEDA: 0.2 detik]

Kedua. Toilet super pintar. Ada tombol pencuci canggih. Wow, bersih banget ya!

[JEDA: 0.2 detik]

Ketiga. Kimchi di mana-mana. Sayuran pedas yang wajib ada. Pedas, tapi enak banget!

[JEDA: 0.2 detik]

Keempat. Angka empat ditakuti. Di lift, sering diganti huruf F. Kayak gak boleh main!

[JEDA: 0.2 detik]

Kelima. Seragam keren ala drama. Bajunya stylish dan kece banget. Mau pakai seragam itu!

[JEDA: 0.2 detik]

Mana fakta yang paling unik? Komen ya!
"""
    
    VOICE_NAME = 'Autonoe'
    BASE_OUTPUT_FILE = 'narasi_2_tts' # Nama file dasar
    FINAL_OUTPUT_FILE = 'final_full_2_narasi.wav'
    # Konfigurasi Chunking (Memaksimalkan RPD)
    MAX_CHARS_PER_CHUNK = 4800 
    
    # Konfigurasi Retry (Memastikan Keberhasilan)
    MAX_RETRIES = 5           # Jumlah upaya sebelum merotasi key/gagal
    BASE_DELAY = 5            # Detik dasar untuk exponential backoff

    try:
        load_api_keys()

        # Panggil fungsi iterasi utama dengan semua argumen
        generate_audio_for_chunks(
            full_prompt=FULL_TEXT_PROMPT, 
            voice=VOICE_NAME, 
            base_filename=BASE_OUTPUT_FILE,
            max_chars_per_chunk=MAX_CHARS_PER_CHUNK,
            max_retries=MAX_RETRIES,      # DARI SINI
            base_delay=BASE_DELAY,        # DARI SINI
            temperature=0.7
        )

        # --- 2. PANGGIL FUNGSI PENGGABUNGAN ---
        combine_audio_chunks(
            base_filename=BASE_OUTPUT_FILE,
            output_filename=FINAL_OUTPUT_FILE
        )

    except Exception as e:
        logger.critical(f"Gagal menjalankan proses utama: {e}")