import tkinter as tk
from tkinter import filedialog
import subprocess
import os
import threading

# constants for window size, padding, and default values
WINDOW_WIDTH = 740
WINDOW_HEIGHT = 260
PADDING = 5
ENTRY_WIDTH = 40
DEFAULT_RESOLUTION = "1920x1080"
DEFAULT_FRAME_RATE = "30"
DEFAULT_TMIX_VALUE = "12"
DEFAULT_BITRATE = "24M"
DEFAULT_INTERPOLATED_FRAMES = "600.0"

class PeterplugBlurApp:
    def __init__(self, root: tk.Tk):
        # initialize the application window
        self.root = root
        self.root.title("Peterplug Blur App")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        # Initialize variables
        self.input_file = None
        self.process = None

        # user input variables with default values
        self.gpu_type = tk.StringVar(value="None")
        self.frame_rate = tk.StringVar(value=DEFAULT_FRAME_RATE)
        self.resolution = tk.StringVar(value=DEFAULT_RESOLUTION)
        self.tmix_value = tk.StringVar(value=DEFAULT_TMIX_VALUE)
        self.bitrate = tk.StringVar(value=DEFAULT_BITRATE)
        self.interpolated_frames = tk.StringVar(value=DEFAULT_INTERPOLATED_FRAMES)

        # breate the application widgets
        self.create_widgets()

        # bind the close event
        self.bind_close_event()

    def create_widgets(self):
        # Create a frame to hold the widgets
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=PADDING)

        # row index to keep track of where we are in the grid
        row_index = 0

        # create menus for user input using the create_radio_buttons method
        self.create_radio_buttons("Resolution:", ["1280x720", "1920x1080", "2560x1440", "3840x2160"], self.resolution, row_index)
        row_index += 1
        self.create_radio_buttons("Frame Rate:", ["18", "24", "30", "60"], self.frame_rate, row_index)
        row_index += 1
        self.create_radio_buttons("Bitrate:", ["16M", "24M", "35M", "53M"], self.bitrate, row_index)
        row_index += 1
        self.create_radio_buttons("Smootness:", ["4", "8", "12", "16"], self.tmix_value, row_index)
        row_index += 1
        self.create_radio_buttons("Interpolated Frames:", ["240.0", "360.0", "480.0", "600.0"], self.interpolated_frames, row_index)
        row_index += 1
        self.create_radio_buttons("GPU Acceleration:", ["None", "NVIDIA", "AMD", "INTEL"], self.gpu_type, row_index)

        # create input file label and entry
        self.create_label_entry("Input File:")

        # start button to begin the blur process
        self.start_button = tk.Button(self.button_frame, text="Start", command=self.start_blur)
        self.start_button.grid(row=row_index + 1, column=4, padx=PADDING, pady=PADDING)

        # Status bar to display messages
        self.status_bar = tk.Label(self.root, text="Select a file and press Start")
        self.status_bar.pack(pady=PADDING)

    def create_radio_buttons(self, label_text, options, variable, row_index):
        #helper function to create radio buttons for user input
        label = tk.Label(self.button_frame, text=label_text)
        label.grid(row=row_index, column=0, padx=PADDING)

        for col_index, option in enumerate(options):
            radio_button = tk.Radiobutton(self.button_frame, text=option, variable=variable, value=option)
            radio_button.grid(row=row_index, column=col_index + 1, padx=PADDING)

    def create_label_entry(self, label_text):
        #Create a label and entry for the input file
        label = tk.Label(self.button_frame, text=label_text)
        label.grid(row=6, column=0, padx=PADDING)

        self.file_entry = tk.Entry(self.button_frame, width=ENTRY_WIDTH)
        self.file_entry.grid(row=6, column=1, columnspan=2, padx=PADDING)
        self.file_entry.bind("<Return>", lambda event: self.select_input_file())

        browse_button = tk.Button(self.button_frame, text="Browse", command=self.select_input_file)
        browse_button.grid(row=6, column=3, padx=PADDING)

    def select_input_file(self):
        #open file dialog to select an input file
        self.input_file = filedialog.askopenfilename()
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, self.input_file)

    def start_blur(self):
        #Start the blur process using FFmpeg
        # check if input file is selected
        if not self.input_file or not os.path.isfile(self.input_file):
            self.status_bar['text'] = "Please select a valid input file"
            return

        # create output file name
        output_file = os.path.join(os.path.dirname(self.input_file), "blur.mp4")
        output_file = os.path.abspath(output_file)  # Ensure absolute file path for output

        # remove existing output file if present
        if os.path.exists(output_file):
            os.remove(output_file)

        # get GPU option
        gpu_option = self.get_gpu_option()

        # build the FFmpeg command
        command = self.build_ffmpeg_command(output_file, gpu_option)

        # disable the start button to prevent multiple clicks
        self.start_button.config(state=tk.DISABLED)

        # create a thread to run FFmpeg
        self.thread = threading.Thread(target=self.run_ffmpeg, args=(command, output_file))
        self.thread.daemon = True  # Allow the thread to exit when the main application closes
        self.thread.start()

    def get_gpu_option(self):
        # return GPU hardware acceleration option based on user selection
        if self.gpu_type.get() == "NVIDIA":
            return "-hwaccel cuda"
        elif self.gpu_type.get() == "AMD":
            return "-hwaccel amf"
        elif self.gpu_type.get() == "INTEL":
            return "-hwaccel qsv"
        return ""  # No GPU acceleration

    def build_ffmpeg_command(self, output_file, gpu_option):
        return (
            f"ffmpeg {gpu_option} -i \"{self.input_file}\" "
            f"-vf \"scale={self.resolution.get()}, "
            f"minterpolate=fps={self.interpolated_frames.get()}, "
            f"tmix=frames={self.tmix_value.get()}:weights=1\" "
            f"-pix_fmt yuv420p -b:v {self.bitrate.get()} "
            f"-r {self.frame_rate.get()} \"{output_file}\""
        )


    def run_ffmpeg(self, command, output_file):
        #run FFmpeg command in a subprocess
        self.status_bar['text'] = "Running FFmpeg..."
        try:
            self.process = subprocess.Popen(command, shell=True)
            self.process.wait()  # Wait for the process to finish

            if self.process.returncode == 0:
                self.status_bar['text'] = f"FFmpeg finished. Output file created: {output_file}"
            else:
                self.status_bar['text'] = "Error: FFmpeg process failed"
        except Exception as e:
            self.status_bar['text'] = f"Error: {str(e)}"
        finally:
            self.start_button.config(state=tk.NORMAL)  # Re-enable the start button

    def bind_close_event(self):
        #Bind the close event to gracefully terminate the process
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        #handle close event and terminate the process if necessary
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.root.destroy()

if __name__ == "__main__":
    # create application window and instance
    root = tk.Tk()
    app = PeterplugBlurApp(root)
    root.mainloop()
