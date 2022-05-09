import wx  # pip install -U --pre -f https://wxpython.org/Phoenix/snapshot-builds/ wxPython
import wx.stc
import codecs
import code_analyzer


class Editor(wx.stc.StyledTextCtrl):
    """Класс текстового поля редактора."""
    def __init__ (self, parent, id = wx.ID_ANY, \
            pos = wx.DefaultPosition, \
            size = wx.DefaultSize,\
            style = 0,\
            name = "editor"):
        wx.stc.StyledTextCtrl.__init__ (self, parent, id, pos, size, style, name)

        # задаём боковую панель с номерами строк
        # TODO: расширение панели
        self.SetMarginWidth(1, 40)
        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(2, 10)

        # создаем кодировщик один раз в конструкторе,
        # чтобы не создавать его при каждой необходимости
        self.encoder = codecs.getencoder("utf-8")

        # стиль по умолчанию
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "size:%d" % 12)

        # определение стилей подсветки
        self.style_def = 0
        self.style_gray = 1
        self.style_purple = 2
        self.style_blue = 3
        self.style_green = 4

        # стили для текста в поле ввода
        self.StyleSetSpec(self.style_def, "face:Consolas,size:12,fore:#000000")
        self.StyleSetSpec(self.style_gray, "face:Consolas,size:12,fore:#888888")
        self.StyleSetSpec(self.style_purple, "face:Consolas,size:12,fore:#C800C8,bold")
        self.StyleSetSpec(self.style_blue, "face:Consolas,size:12,fore:#000096,bold")
        self.StyleSetSpec(self.style_green, "face:Consolas,size:12,fore:#009600,italic")

        self.code_analyzer = code_analyzer.CodeAnalyzer()

        # подписка на событие, когда нужно изменить стиль
        self.Bind(wx.stc.EVT_STC_STYLENEEDED, self.onStyleNeed)

        self.analyzed = None  # список кортежей с результатом анализа текста

        # подписка на событие "Добавление символа"
        # self.Bind (wx.stc.EVT_STC_CHARADDED, self.onCharAdded)


    def onCharAdded(self, event):
        # получим код нажатой клавиши
        key_val = event.GetKey()

         # нас не интересуют нажатые клавиши с кодом больше 127
        if key_val>127:
            return

        # получим символ нажатой клавиши
        key = chr(key_val)

        if key == self.code_analyzer.QUOTE:
            pos = self.GetCurrentPos()
            # дописываем закрывающуюся кавычку
            self.AddText(self.code_analyzer.QUOTE)
            # установим каретку перед закрывающейся кавычкой
            self.GotoPos(pos)


    def onPosChange (self, event):
        # Получим текущую позицию каретки в байтах
        pos = self.GetCurrentPos()
        text_left = self.GetTextRange(0, pos)
        self.GetParent().GetParent().GetParent().SetTitle(str (len (text_left) ) )


    def calcByteLen(self, text):
        """Посчитать длину строки в байтах, а не в символах"""
        return len(self.encoder(text)[0])


    def calcBytePos(self, text, pos):
        """Преобразовать позицию в символах в позицию в байтах"""
        return len(self.encoder(text[:pos])[0])


    def onStyleNeed(self, event):
        """Подсветка синтаксиса."""
        text = self.GetText()

        # cначала ко всему тексту применим стиль по умолчанию
        self.StartStyling(0)
        self.SetStyling(self.calcByteLen(text), self.style_def)

        analyzed, completion = self.code_analyzer.get_words(text)

        if completion:
            self.AddText(completion)
        # self.SetCurrentPos(len(completed_code))

        for word, line_number, last_pos, word_type in analyzed:
            pos = last_pos-len(word)
            bytepos = self.calcBytePos(text, pos)  # находим начальную позицию в байтах
            text_byte_len = self.calcByteLen(word)  # вычисляем длину слова в байтах
            # применяем стиль
            self.StartStyling(bytepos)
            if word_type == self.code_analyzer.STRING:
                self.SetStyling(text_byte_len, self.style_green)
            elif word_type == self.code_analyzer.COMMENT:
                self.SetStyling(text_byte_len, self.style_gray)
            elif word_type == self.code_analyzer.KEYWORD:
                if word == self.code_analyzer.BOT or word == self.code_analyzer.BOT_END or\
                   word == self.code_analyzer.SCENE or word == self.code_analyzer.SCENE_END:
                    self.SetStyling(text_byte_len, self.style_purple)
                else:
                    self.SetStyling(text_byte_len, self.style_blue)

        self.analyzed = self.code_analyzer.get_words_for_parsing(analyzed)
        # print(analyzed)
        # print(self.code_analyzer.get_words_for_parsing(analyzed))


class MainWindow(wx.Frame):
    """Класс окна редактора."""
    def __init__(self, parent, title):
        super().__init__(parent, title=title, style = wx.DEFAULT_FRAME_STYLE | wx.MAXIMIZE)
        # TODO: иконка
        # TODO: отступы меню
        # иконки меню
        self.createMenuBar()
        self.createSideBar()

        self.main_spltr = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_LIVE_UPDATE)

        self.sidebar_p = wx.Panel(self.main_spltr)
        self.edit_p = wx.Panel(self.main_spltr)

        self.main_spltr.SplitVertically(self.sidebar_p, self.edit_p)
        self.main_spltr.SetMinimumPaneSize(200)

        self.scenes_p = wx.Panel(self.sidebar_p)
        self.scenes_st = wx.StaticText(self.scenes_p, label='Сцены')
        self.scenes_b = wx.Button(self.scenes_p, label='+', style=wx.BU_EXACTFIT)
        self.scenes_lb = wx.ListBox(self.scenes_p, choices=self.get_scenes_names())
        self.scenes_gbs = wx.GridBagSizer(2, 3)
        self.scenes_gbs.Add(self.scenes_st, pos=(0, 0))
        self.scenes_gbs.Add(self.scenes_b, pos=(0, 2))
        self.scenes_gbs.Add(self.scenes_lb, pos=(1, 0), span=(1, 3), flag=wx.EXPAND | wx.UP, border=5)
        self.scenes_gbs.AddGrowableCol(1)
        self.scenes_gbs.AddGrowableRow(1)
        self.scenes_p.SetSizer(self.scenes_gbs)

        self.res_p = wx.Panel(self.sidebar_p)
        self.res_st = wx.StaticText(self.res_p, label='Ресурсы')
        self.res_b = wx.Button(self.res_p, label='+', style=wx.BU_EXACTFIT)
        self.res_lb = wx.ListBox(self.res_p, choices=self.get_resources_names())
        self.res_gbs = wx.GridBagSizer(2, 3)
        self.res_gbs.Add(self.res_st, pos=(0, 0))
        self.res_gbs.Add(self.res_b, pos=(0, 2))
        self.res_gbs.Add(self.res_lb, pos=(1, 0), span=(1, 3), flag=wx.EXPAND | wx.UP, border=5)
        self.res_gbs.AddGrowableCol(1)
        self.res_gbs.AddGrowableRow(1)
        self.res_p.SetSizer(self.res_gbs)

        self.sidebar_bs = wx.BoxSizer(wx.VERTICAL)
        self.sidebar_bs.Add(self.scenes_p, wx.ID_ANY, flag=wx.EXPAND | wx.ALL, border=5)
        self.sidebar_bs.Add(self.res_p, wx.ID_ANY, flag=wx.EXPAND | wx.ALL, border=5)
        self.sidebar_p.SetSizer(self.sidebar_bs)

        self.editor = Editor(self.edit_p)
        self.edit_bs = wx.BoxSizer()
        self.edit_bs.Add(self.editor, wx.ID_ANY, flag=wx.EXPAND)
        self.edit_p.SetSizer(self.edit_bs)
        # scenes_header_p = wx.Panel(sidebar_p)
        # scenes_header_st = wx.StaticText(scenes_header_p, label='Сцены:')
        # scenes_header_b = wx.Button(scenes_header_p, label='+', style=wx.BU_EXACTFIT)
        # scenes_header_bs = wx.BoxSizer(wx.HORIZONTAL)
        # scenes_header_bs.Add(scenes_header_st)
        # scenes_header_bs.Add(wx.StaticText(scenes_header_p), flag=wx.EXPAND)
        # scenes_header_bs.Add(scenes_header_b)

        # scenes_lb = wx.ListBox(sidebar_p, choices=self.get_scenes_names())

        # sidebar_bs = wx.BoxSizer(wx.VERTICAL)
        # sidebar_bs.Add(scenes_header_p, flag=wx.EXPAND | wx.ALL, border=10)
        # sidebar_bs.Add(wx.StaticLine(sidebar_p), flag=wx.EXPAND | wx.ALL, border=10)
        # sidebar_bs.Add(scenes_lb, flag=wx.EXPAND | wx.ALL, border=10)

        # edit_tc = wx.TextCtrl(main_p, style=wx.TE_MULTILINE)

        # sidebar_bs.Add(edit, proportion=1)
        # scenes_header_p.SetSizer(scenes_header_bs)
        # sidebar_p.SetSizer(sidebar_bs)



    def createMenuBar(self):
        self.menubar = wx.MenuBar()

        # TODO: свои ID
        self.project_menu = wx.Menu()  # вкладка "Проект"
        self.create_item = self.project_menu.Append(wx.ID_ANY, 'Создать\tCtrl+N', 'Создать новый пустой проект')
        self.open_item = self.project_menu.Append(wx.ID_ANY, 'Открыть...\tCtrl+O', 'Открыть существующий проект')
        self.save_item = self.project_menu.Append(wx.ID_ANY, 'Сохранить...\tCtrl+S', 'Сохранить изменения в текущем проекте')

        self.bot_menu = wx.Menu()  # подменю "Бот"
        self.start_item = self.bot_menu.Append(wx.ID_ANY, 'Запуск...\tCtrl+K', 'Запустить бота')
        self.stop_item = self.bot_menu.Append(wx.ID_ANY, 'Стоп\tCtrl+P', 'Остановить бота')

        self.about_menu = wx.Menu()  # вкладка "О программе"
        self.doc_item = self.about_menu.Append(wx.ID_ANY, 'Спецификация языка\tCtrl+D', 'Просмотреть команды языка разметки сценариев')
        self.help_item = self.about_menu.Append(wx.ID_ANY, 'Руководство пользователя\tCtrl+H', 'Посмотреть руководство пользователя')

        self.menubar.Append(self.project_menu, '&Проект')
        self.menubar.Append(self.bot_menu, '&Бот')
        self.menubar.Append(self.about_menu, '&Помощь')

        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.onCreateClick, self.create_item)
        self.Bind(wx.EVT_MENU, self.onOpenClick, self.open_item)
        self.Bind(wx.EVT_MENU, self.onSaveClick, self.save_item)
        self.Bind(wx.EVT_MENU, self.onStartClick, self.start_item)
        self.Bind(wx.EVT_MENU, self.onStopClick, self.stop_item)
        self.Bind(wx.EVT_MENU, self.onDocClick, self.doc_item)
        self.Bind(wx.EVT_MENU, self.onHelpClick, self.help_item)

    def createSideBar(self):
        pass

    def get_scenes_names(self):
        return ['сцена 1', 'сцена 2', 'сцена 3']*10  # TODO: реализовать

    def get_resources_names(self):
        return ['pic.jpg', 'video.mp4', 'voice.ogg']  # TODO: реализовать

    def onCreateClick(self, event):
        pass

    def onOpenClick(self, event):
        pass

    def onSaveClick(self, event):
        pass

    def onStartClick(self, event):
        print('Собираем бота...')
        analyzed = self.editor.analyzed
        pass

    def onStopClick(self, event):
        pass

    def onDocClick(self, event):
        pass

    def onHelpClick(self, event):
        pass

app = wx.App()

frame = MainWindow(None, 'Редактор Telegram-ботов')
frame.Show()

app.MainLoop()