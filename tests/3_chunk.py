from google import genai
from google.genai import types
from google.genai.errors import APIError
import wave
import time
import logging
import os

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
def split_text_into_chunks(full_text: str, paragraphs_per_chunk: int = 3) -> list[str]:
    """
    Membagi teks menjadi chunk berdasarkan paragraf (baris kosong).
    """
    # Pisahkan teks menjadi paragraf individual
    paragraphs = [p.strip() for p in full_text.split('\n') if p.strip()]
    
    chunks = []
    # Loop untuk mengelompokkan 3 paragraf menjadi satu chunk
    for i in range(0, len(paragraphs), paragraphs_per_chunk):
        chunk = ' '.join(paragraphs[i:i + paragraphs_per_chunk])
        chunks.append(chunk)
        
    logger.info(f"Teks dibagi menjadi {len(chunks)} chunk.")
    return chunks

# Asumsikan semua import, load_api_keys, get_current_api_key, rotate_api_key, 
# dan make_tts_request_with_retry sudah didefinisikan dengan perbaikan terakhir Anda.

# --- Fungsi Iterasi Utama ---
def generate_audio_for_chunks(full_prompt: str, voice: str, base_filename: str, 
                              paragraphs_per_chunk: int = 3, temperature: float = 0.7):
    """
    Memecah teks menjadi chunk dan menghasilkan audio untuk setiap chunk 
    dengan mekanisme rotasi API key.
    """
    
    # 1. Membagi Teks
    text_chunks = split_text_into_chunks(full_prompt, paragraphs_per_chunk)
    
    total_chunks = len(text_chunks)
    
    # 2. Iterasi dan Generasi Audio
    for i, chunk in enumerate(text_chunks):
        logger.info(f"\n--- Memproses Chunk {i + 1} dari {total_chunks} ---")
        
        # Panggil fungsi TTS dengan retry dan rotasi
        make_tts_request_with_retry(
            prompt=chunk, 
            voice=voice, 
            # Memberikan base_filename dan indeks untuk penamaan unik
            base_filename=base_filename,
            chunk_index=i + 1,
            temperature=temperature
        )
        
        # Opsional: Jeda singkat antar permintaan untuk menghindari rate-limit
        time.sleep(0.5)

# --- Fungsi Utama dengan Rotasi Key ---
def make_tts_request_with_retry(prompt: str, voice: str, base_filename: str, chunk_index: int, temperature: float = 0.7):
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

            
            try:
                data = response.candidates[0].content.parts[0].inline_data.data
            except (AttributeError, IndexError) as e:
                # Jika pengambilan data gagal, kita putar key dan coba lagi
                logger.error(f'❌ Gagal mengambil data audio. Rotasi key. Error: {e}')
                raise APIError("Gagal parsing respons audio.") # Lempar error API untuk memicu rotasi
                
            # Menyimpan File
            save_audio_to_wav(base_filename, data, chunk_index)
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
    # ... (load_api_keys) ...
    
    FULL_TEXT_PROMPT = """
Ini adalah paragraf pertama. Paragraf ini pendek dan hanya sebagai contoh.
    
Paragraf kedua. Kita harus memastikan sistem TTS kita bekerja dengan sempurna meskipun ada rotasi API key yang terjadi di tengah proses.
    
Paragraf ketiga. Chunk pertama akan berakhir di sini.    
    """
    
    VOICE_NAME = 'Kore'
    BASE_OUTPUT_FILE = 'narasi_tts' # Nama file dasar (akan menjadi narasi_tts_01.wav, narasi_tts_02.wav, dst.)
    PARAGRAPHS_PER_CHUNK = 1
    
    try:
        load_api_keys()
        
        # Panggil fungsi iterasi utama
        generate_audio_for_chunks(
            full_prompt=FULL_TEXT_PROMPT, 
            voice=VOICE_NAME, 
            base_filename=BASE_OUTPUT_FILE,
            paragraphs_per_chunk=PARAGRAPHS_PER_CHUNK,
            temperature=0.7
        )
        
    except Exception as e:
        logger.critical(f"Gagal menyelesaikan proses generasi audio: {e}")