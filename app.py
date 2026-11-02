import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class VoiceSeparatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Separador de Voz")
        self.root.geometry("620x360")
        self.root.minsize(540, 320)

        self.video_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status = tk.StringVar(value="Selecione um vídeo para começar.")
        self.progress_text = tk.StringVar(value="0%")
        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.process_lock = threading.Lock()
        self.active_process = None

        self._build_ui()
        self.root.after(100, self._process_events)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=24)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Separador de Voz", font=("Segoe UI", 20, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            frame,
            text="Escolha um vídeo e extraia a voz da música para um arquivo WAV.",
            wraplength=560,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 22))

        ttk.Label(frame, text="Vídeo").grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Entry(frame, textvariable=self.video_path, state="readonly").grid(
            row=3, column=0, sticky="ew", pady=(5, 14), padx=(0, 10)
        )
        self.video_button = ttk.Button(frame, text="Escolher vídeo...", command=self._choose_video)
        self.video_button.grid(row=3, column=1, sticky="ew", pady=(5, 14))

        ttk.Label(frame, text="Salvar voz como").grid(row=4, column=0, columnspan=2, sticky="w")
        ttk.Entry(frame, textvariable=self.output_path, state="readonly").grid(
            row=5, column=0, sticky="ew", pady=(5, 18), padx=(0, 10)
        )
        self.output_button = ttk.Button(
            frame, text="Escolher destino...", command=self._choose_output
        )
        self.output_button.grid(row=5, column=1, sticky="ew", pady=(5, 18))

        actions = ttk.Frame(frame)
        actions.grid(row=6, column=0, columnspan=2, sticky="ew")
        actions.columnconfigure(0, weight=1)
        self.start_button = ttk.Button(
            actions, text="Separar voz", command=self._start_separation
        )
        self.start_button.grid(row=0, column=0, sticky="w")
        self.cancel_button = ttk.Button(
            actions, text="Cancelar", command=self._cancel, state="disabled"
        )
        self.cancel_button.grid(row=0, column=1, sticky="e")

        progress_frame = ttk.Frame(frame)
        progress_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(18, 8))
        progress_frame.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(progress_frame, mode="determinate", maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Label(progress_frame, textvariable=self.progress_text, width=5, anchor="e").grid(
            row=0, column=1, sticky="e"
        )
        ttk.Label(frame, textvariable=self.status, wraplength=560).grid(
            row=8, column=0, columnspan=2, sticky="w"
        )

    def _choose_video(self):
        path = filedialog.askopenfilename(
            title="Escolher vídeo",
            filetypes=[
                ("Vídeos", "*.mp4 *.mkv *.mov *.avi *.webm *.m4v"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not path:
            return
        self.video_path.set(path)
        self.output_path.set(str(Path(path).with_name(f"{Path(path).stem}_voz.wav")))

    def _choose_output(self):
        video = self.video_path.get()
        initial_name = f"{Path(video).stem}_voz.wav" if video else "voz.wav"
        path = filedialog.asksaveasfilename(
            title="Salvar áudio da voz",
            defaultextension=".wav",
            initialfile=initial_name,
            filetypes=[("Áudio WAV", "*.wav")],
        )
        if path:
            self.output_path.set(path)

    def _start_separation(self):
        video = Path(self.video_path.get()) if self.video_path.get() else None
        output = Path(self.output_path.get()) if self.output_path.get() else None
        if video is None or not video.is_file():
            messagebox.showerror("Vídeo não selecionado", "Escolha um arquivo de vídeo válido.")
            return
        if output is None:
            messagebox.showerror("Destino não selecionado", "Escolha onde salvar o áudio.")
            return
        if video.resolve() == output.resolve():
            messagebox.showerror("Destino inválido", "O arquivo de saída não pode ser o vídeo.")
            return

        self.cancel_event.clear()
        self.progress.configure(value=0)
        self.progress_text.set("0%")
        self._set_running(True)
        self.status.set("Preparando a separação...")
        threading.Thread(
            target=self._separate, args=(video, output), daemon=True
        ).start()

    def _separate(self, video, output):
        try:
            ffmpeg = self._find_ffmpeg()
            output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="separador_voz_") as temporary:
                temporary_path = Path(temporary)
                extracted_audio = temporary_path / "entrada.wav"
                self._run_process(
                    [
                        ffmpeg,
                        "-y",
                        "-i",
                        str(video),
                        "-vn",
                        "-ac",
                        "2",
                        "-ar",
                        "44100",
                        "-c:a",
                        "pcm_s16le",
                        "-progress",
                        "pipe:1",
                        "-nostats",
                        str(extracted_audio),
                    ],
                    "Extraindo o áudio do vídeo...",
                    progress_range=(0, 10),
                )
                self._check_cancelled()

                self._run_process(
                    [
                        self._console_python(),
                        "-c",
                        "import runpy, sys; sys.stderr.isatty = lambda: True; runpy.run_module('demucs', run_name='__main__')",
                        "--two-stems=vocals",
                        "--name",
                        "htdemucs",
                        "--out",
                        str(temporary_path / "separado"),
                        str(extracted_audio),
                    ],
                    "Separando voz e instrumentos. Isso pode levar alguns minutos...",
                    progress_range=(10, 95),
                )
                self._check_cancelled()

                vocal_track = (
                    temporary_path / "separado" / "htdemucs" / "entrada" / "vocals.wav"
                )
                if not vocal_track.is_file():
                    raise RuntimeError(
                        "A separação terminou, mas o arquivo de voz não foi encontrado."
                    )
                shutil.copy2(vocal_track, output)

            self.events.put(("progress", 100))
            self.events.put(("success", str(output)))
        except SeparationCancelled:
            self.events.put(("cancelled", None))
        except (OSError, RuntimeError) as error:
            self.events.put(("error", str(error)))
        finally:
            with self.process_lock:
                self.active_process = None

    def _find_ffmpeg(self):
        executable = shutil.which("ffmpeg")
        if executable:
            return executable
        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()
        except (ImportError, RuntimeError) as error:
            raise RuntimeError(
                "FFmpeg não foi encontrado. Instale as dependências pelo arquivo "
                "instalar.bat e tente novamente."
            ) from error

    def _console_python(self):
        executable = Path(sys.executable).with_name("python.exe")
        return str(executable) if executable.is_file() else sys.executable

    def _run_process(self, command, status, progress_range=None):
        self.events.put(("status", status))
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as error:
            raise RuntimeError(f"Não foi possível iniciar o processamento: {error}") from error

        with self.process_lock:
            self.active_process = process
        try:
            messages = []
            line_buffer = ""
            duration = None
            last_progress = progress_range[0] if progress_range else None
            if process.stdout is not None:
                while True:
                    character = process.stdout.read(1)
                    if not character:
                        if line_buffer:
                            last_progress = self._consume_output_line(
                                line_buffer,
                                messages,
                                progress_range,
                                duration,
                                last_progress,
                            )
                        break
                    if character in ("\r", "\n"):
                        if line_buffer:
                            duration = self._read_duration(line_buffer) or duration
                            last_progress = self._consume_output_line(
                                line_buffer,
                                messages,
                                progress_range,
                                duration,
                                last_progress,
                            )
                            line_buffer = ""
                    else:
                        line_buffer += character
                    if self.cancel_event.is_set():
                        process.terminate()
                        break
            return_code = process.wait()
        finally:
            with self.process_lock:
                if self.active_process is process:
                    self.active_process = None

        if self.cancel_event.is_set():
            raise SeparationCancelled()
        if return_code != 0:
            detail = "\n".join(messages[-4:])
            if "No module named demucs" in detail:
                raise RuntimeError(
                    "O Demucs não está instalado neste ambiente. Feche o aplicativo, "
                    "execute instalar.bat e abra iniciar.bat novamente."
                )
            if "No such file or directory" in detail or "No audio" in detail:
                raise RuntimeError(
                    "Não foi possível encontrar uma faixa de áudio no vídeo."
                )
            raise RuntimeError(
                "O processamento falhou. Confira se o vídeo contém áudio e tente novamente."
                + (f"\n\nDetalhes:\n{detail}" if detail else "")
            )

    def _read_duration(self, line):
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", line)
        if not match:
            return None
        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    def _consume_output_line(
        self, line, messages, progress_range, duration, last_progress
    ):
        line = line.strip()
        if line:
            messages.append(line)
            del messages[:-8]

        if not progress_range:
            return last_progress

        start, end = progress_range
        current = None
        if start == 0:
            time_match = re.search(r"out_time=(\d+):(\d+):(\d+(?:\.\d+)?)", line)
            if time_match and duration:
                hours, minutes, seconds = time_match.groups()
                elapsed = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                current = start + (end - start) * min(elapsed / duration, 1)
        else:
            match = re.search(r"\b(\d{1,3})%\|", line)
            if match:
                current = start + (end - start) * int(match.group(1)) / 100

        if current is not None:
            current = min(end, max(last_progress, round(current)))
            if current > last_progress:
                self.events.put(("progress", current))
                return current
        return last_progress

    def _check_cancelled(self):
        if self.cancel_event.is_set():
            raise SeparationCancelled()

    def _cancel(self):
        self.cancel_event.set()
        with self.process_lock:
            process = self.active_process
        if process is not None and process.poll() is None:
            process.terminate()
        self.status.set("Cancelando...")
        self.cancel_button.configure(state="disabled")

    def _set_running(self, running):
        self.video_button.configure(state="disabled" if running else "normal")
        self.output_button.configure(state="disabled" if running else "normal")
        self.start_button.configure(state="disabled" if running else "normal")
        self.cancel_button.configure(state="normal" if running else "disabled")

    def _process_events(self):
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == "status":
                    self.status.set(value)
                elif event == "progress":
                    self.progress.configure(value=value)
                    self.progress_text.set(f"{value}%")
                elif event == "success":
                    self._set_running(False)
                    self.status.set("Voz separada com sucesso.")
                    messagebox.showinfo(
                        "Concluído", f"O áudio da voz foi salvo em:\n{value}"
                    )
                elif event == "error":
                    self._set_running(False)
                    self.status.set("Não foi possível concluir a separação.")
                    messagebox.showerror("Erro na separação", value)
                elif event == "cancelled":
                    self._set_running(False)
                    self.status.set("Separação cancelada.")
        except queue.Empty:
            pass
        self.root.after(100, self._process_events)

    def _on_close(self):
        with self.process_lock:
            process = self.active_process
        if process is not None and process.poll() is None:
            self.cancel_event.set()
            process.terminate()
        self.root.destroy()


class SeparationCancelled(Exception):
    pass


if __name__ == "__main__":
    root = tk.Tk()
    VoiceSeparatorApp(root)
    root.mainloop()
