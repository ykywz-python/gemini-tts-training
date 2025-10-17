from google import genai
from google.genai import types
from google.genai.errors import APIError
import wave
import time
import logging

# --- Konfigurasi Global dan API Key Management ---

# Konfigurasi Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# --- Fungsi Utility WAV ---
def save_audio_to_wav(filename: str, pcm_data: bytes, channels=1, rate=24000, sample_width=2):
    """Menulis data PCM audio biner ke file WAV."""
    try:
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)
        logger.info(f"✅ File audio berhasil disimpan ke: {filename}")
    except Exception as e:
        logger.error(f"❌ Error saat menyimpan file WAV: {e}")

# --- Fungsi Utama dengan Rotasi Key ---
def make_tts_request_with_retry(prompt: str, voice: str, filename: str, temperature: float = 0.7):
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
            logger.info(f'Mencoba request ke Gemini dengan API Key index: {current_api_key_index} (Percobaan {attempt + 1}/{max_retries})')
            
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

            # Mengambil Data Audio
            data = response.candidates[0].content.parts[0].inline_data.data
            
            # Menyimpan dan Mengakhiri
            save_audio_to_wav(filename, data)
            return

        except APIError as e:
            # Error API lainnya (misal: invalid argument, server error)
            logger.error(f'❌ Error API lain pada Key Index {current_api_key_index}: {e}')
            # Untuk error API selain kuota, kita putar key dan coba lagi
            if attempt + 1 < max_retries:
                rotate_api_key()
                time.sleep(1)
            else:
                raise e # Jika semua key gagal, lempar error terakhir
                
        except Exception as e:
            # Error non-API (misal: error I/O file, error parsing response)
            logger.error(f'❌ Error tak terduga: {e}')
            raise e


# --- Eksekusi Script ---
if __name__ == "__main__":
    # 📝 PASTIKAN ANDA MEMILIKI FILE 'api-keys.txt' DENGAN SATU KEY PER BARIS!
    
    try:
        load_api_keys()
        
        PROMPT = "Say angry: We successfully implemented the API key rotation mechanism!"
        VOICE_NAME = 'Kore'
        OUTPUT_FILE = 'out_rotated.wav'
        
        make_tts_request_with_retry(
            prompt=PROMPT, 
            voice=VOICE_NAME, 
            filename=OUTPUT_FILE,
            temperature=0.7
        )
        
    except (FileNotFoundError, ValueError, Exception) as e:
        logger.critical(f"Gagal menjalankan script: {e}")