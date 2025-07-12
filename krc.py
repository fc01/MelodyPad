import sys
import mido
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

class KRCConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.midi_path = ""
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('MIDI + 歌词 -> KRC 转换器')
        self.setGeometry(300, 300, 700, 600)

        # 整体垂直布局
        main_layout = QVBoxLayout()

        # --- MIDI 文件输入部分 ---
        midi_layout = QHBoxLayout()
        midi_label = QLabel("MIDI 文件:")
        self.midi_path_input = QLineEdit()
        self.midi_path_input.setReadOnly(True)
        self.midi_path_input.setPlaceholderText("请选择一个 .mid 文件")
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_midi_file)
        
        midi_layout.addWidget(midi_label)
        midi_layout.addWidget(self.midi_path_input)
        midi_layout.addWidget(browse_button)

        # --- 歌词输入部分 ---
        lyrics_label = QLabel("歌词 (每行对应一段旋律):")
        self.lyrics_input = QTextEdit()
        self.lyrics_input.setPlaceholderText(
            "在这里输入歌词，一行歌词对应一段连续的音符。\n"
            "例如：\n"
            "一闪一闪亮晶晶\n"
            "满天都是小星星"
        )
        self.lyrics_input.setMinimumHeight(150)

        # --- 转换按钮 ---
        convert_button = QPushButton("转换")
        convert_button.setStyleSheet("font-size: 16px; padding: 10px;")
        convert_button.clicked.connect(self.convert_to_krc)

        # --- KRC 输出部分 ---
        output_label = QLabel("KRC 输出结果:")
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("转换后的 KRC 格式内容将显示在这里")
        self.output_text.setMinimumHeight(150)

        # 将所有组件添加到主布局
        main_layout.addLayout(midi_layout)
        main_layout.addWidget(lyrics_label)
        main_layout.addWidget(self.lyrics_input)
        main_layout.addWidget(convert_button, 0, Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(output_label)
        main_layout.addWidget(self.output_text)

        self.setLayout(main_layout)

    def browse_midi_file(self):
        """打开文件对话框选择MIDI文件"""
        file_name, _ = QFileDialog.getOpenFileName(self, "选择 MIDI 文件", "", "MIDI 文件 (*.mid *.midi)")
        if file_name:
            self.midi_path = file_name
            self.midi_path_input.setText(file_name)

    def parse_midi_to_notes(self, midi_path):
        """
        解析MIDI文件，提取音符的开始时间和持续时间（毫秒）。
        返回一个字典对象数组，例如: [{'start': 100, 'duration': 200, 'note': 60}]
        """
        try:
            mid = mido.MidiFile(midi_path)
            ticks_per_beat = mid.ticks_per_beat
            
            # 寻找 tempo (节拍速度), 默认为 120 BPM
            tempo = 500000  # microseconds per beat
            for msg in mid:
                if msg.is_meta and msg.type == 'set_tempo':
                    tempo = msg.tempo
                    break
            
            notes = []
            open_notes = {}  # 记录已触发但未结束的音符
            absolute_time_ticks = 0

            # 通常音符轨道在第一个或第二个轨道
            for msg in mid.tracks[1]: # 假设音符在第二个轨道（常见）
                absolute_time_ticks += msg.time

                if msg.type == 'note_on' and msg.velocity > 0:
                    open_notes[msg.note] = absolute_time_ticks
                
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in open_notes:
                        start_ticks = open_notes.pop(msg.note)
                        duration_ticks = absolute_time_ticks - start_ticks
                        
                        start_ms = int(mido.tick2second(start_ticks, ticks_per_beat, tempo) * 1000)
                        duration_ms = int(mido.tick2second(duration_ticks, ticks_per_beat, tempo) * 1000)
                        
                        if duration_ms > 0: # 忽略时长为0的音符
                            notes.append({
                                'start': start_ms,
                                'duration': duration_ms,
                                'note': msg.note
                            })
            
            # 按开始时间排序
            notes.sort(key=lambda x: x['start'])
            return notes

        except Exception as e:
            self.show_error_message(f"MIDI文件解析失败: {e}")
            return None

    def generate_krc_string(self, notes, lyrics):
        """将音符数据和歌词转换为KRC格式字符串"""
        lyrics_lines = [line.strip() for line in lyrics.strip().split('\n') if line.strip()]
        if not lyrics_lines:
            return ""

        krc_output_lines = []
        note_index = 0
        
        for line in lyrics_lines:
            # 移除歌词中的空格，因为KRC通常不处理空格
            clean_line = line.replace(" ", "")
            num_chars = len(clean_line)

            if note_index + num_chars > len(notes):
                self.show_error_message(f"错误：歌词 '{line}' 的字数 ({num_chars}) 超出剩余音符数量。")
                break
            
            line_notes = notes[note_index : note_index + num_chars]
            if not line_notes:
                continue

            # 计算行开始时间和总时长
            line_start_time = line_notes[0]['start']
            line_end_time = line_notes[-1]['start'] + line_notes[-1]['duration']
            line_total_duration = line_end_time - line_start_time
            
            # 构建行头部 [开始时间,总时长]
            krc_line = f"[{line_start_time},{line_total_duration}]"

            # 构建每个字的时间 <字,时长,0>
            for i, char in enumerate(clean_line):
                note = line_notes[i]
                char_duration = note['duration']
                krc_line += f"<{char},{char_duration},0>"
            
            krc_output_lines.append(krc_line)
            note_index += num_chars
        
        # 添加KRC文件头信息（可选，但规范）
        krc_header = [
            "[ti:歌曲标题]",
            "[ar:歌手]",
            "[al:专辑]",
            "[by:KRC转换器]",
            "[offset:0]"
        ]
        
        return "\n".join(krc_header + krc_output_lines)

    def convert_to_krc(self):
        """点击转换按钮时执行的核心逻辑"""
        # 1. 输入验证
        if not self.midi_path:
            self.show_error_message("请先选择一个 MIDI 文件。")
            return
        
        lyrics_text = self.lyrics_input.toPlainText()
        if not lyrics_text.strip():
            self.show_error_message("请输入歌词。")
            return

        # 2. 加载和解析 MIDI 文件
        notes = self.parse_midi_to_notes(self.midi_path)
        if notes is None or not notes:
            if notes is not None: # 如果是空列表
                 self.show_error_message("在MIDI文件中没有找到有效的音符数据。请检查轨道或文件内容。")
            return

        # 3. 生成 KRC 字符串
        krc_content = self.generate_krc_string(notes, lyrics_text)

        # 4. 显示到 output 文本框
        self.output_text.setText(krc_content)
        if krc_content:
             QMessageBox.information(self, "成功", "KRC 文件内容已成功生成！")


    def show_error_message(self, message):
        """显示一个错误消息弹窗"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("错误")
        msg_box.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KRCConverterApp()
    window.show()
    sys.exit(app.exec())