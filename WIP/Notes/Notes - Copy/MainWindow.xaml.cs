using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace Notes
{
    public partial class MainWindow : Window
    {
        private ObservableCollection<Note> Notes = new ObservableCollection<Note>();
        private const string NotesDirectory = "Notities";
        private Note currentNote = null;
        private bool isEditing = false;

        public MainWindow()
        {
            InitializeComponent();
            Directory.CreateDirectory(NotesDirectory);
            LoadNotes();
            NotesList.ItemsSource = Notes;
        }

        public class Note
        {
            public string Title { get; set; }
            public string Content { get; set; }
        }

        private void LoadNotes()
        {
            var files = Directory.GetFiles(NotesDirectory, "*.*", SearchOption.TopDirectoryOnly);
            foreach (var file in files)
            {
                var title = Path.GetFileName(file);
                var content = File.ReadAllText(file);
                Notes.Add(new Note { Title = title, Content = content });
            }
        }

        private void AddNewNote_Click(object sender, RoutedEventArgs e)
        {
            var newNote = new Note { Title = "NieuweNotitie.txt", Content = "" };
            Notes.Add(newNote);
            currentNote = newNote;
            isEditing = true;

            AddNewNoteButton.Visibility = Visibility.Collapsed;
            FileNameTextBox.Text = "NieuweNotitie";
            FileExtensionTextBox.Text = ".txt";
            FileNamePanel.Visibility = Visibility.Visible;
            NoteContentTextBox.Text = newNote.Content;
            NoteContentTextBox.IsReadOnly = false;
            NoteTitleTextBox.Visibility = Visibility.Visible;
            NoteContentTextBox.Visibility = Visibility.Visible;
            SaveButton.Visibility = Visibility.Visible;
            NotesList.Visibility = Visibility.Collapsed;
        }

        private void EditNote_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.CommandParameter is Note note)
            {
                currentNote = note;
                FileNameTextBox.Text = Path.GetFileNameWithoutExtension(note.Title);
                FileExtensionTextBox.Text = Path.GetExtension(note.Title);
                NoteTitleTextBox.Text = note.Title;
                NoteContentTextBox.Text = note.Content;
                NoteTitleTextBox.IsReadOnly = false;
                NoteContentTextBox.IsReadOnly = false;

                isEditing = true;

                AddNewNoteButton.Visibility = Visibility.Collapsed;
                FileNamePanel.Visibility = Visibility.Visible;
                NoteTitleTextBox.Visibility = Visibility.Visible;
                NoteContentTextBox.Visibility = Visibility.Visible;
                SaveButton.Visibility = Visibility.Visible;
                NotesList.Visibility = Visibility.Collapsed;
            }
        }

        private void SaveNote_Click(object sender, RoutedEventArgs e)
        {
            if (currentNote != null && isEditing)
            {
                string oldTitle = currentNote.Title;
                string newTitle = FileNameTextBox.Text;

                // Voeg een punt toe als de extensie dat niet heeft
                string extension = FileExtensionTextBox.Text.StartsWith(".")
                    ? FileExtensionTextBox.Text
                    : "." + FileExtensionTextBox.Text;

                newTitle += extension;
                string newContent = NoteContentTextBox.Text;

                // Update note properties
                currentNote.Title = newTitle;
                currentNote.Content = newContent;

                // Rename the file if the title has changed
                if (oldTitle != newTitle)
                {
                    string oldFilePath = Path.Combine(NotesDirectory, oldTitle);
                    string newFilePath = Path.Combine(NotesDirectory, newTitle);

                    if (File.Exists(oldFilePath))
                    {
                        File.Move(oldFilePath, newFilePath);
                    }
                }

                SaveNoteToFile(currentNote);

                NotesList.Items.Refresh();
                MessageBox.Show("Notitie opgeslagen!");

                NoteTitleTextBox.Visibility = Visibility.Collapsed;
                NoteContentTextBox.Visibility = Visibility.Collapsed;
                FileNamePanel.Visibility = Visibility.Collapsed;
                SaveButton.Visibility = Visibility.Collapsed;
                NotesList.Visibility = Visibility.Visible;
                AddNewNoteButton.Visibility = Visibility.Visible;

                isEditing = false;
            }
        }


        private void SaveNoteToFile(Note note)
        {
            var filePath = Path.Combine(NotesDirectory, note.Title);
            File.WriteAllText(filePath, note.Content);
        }

        private void ClearPlaceholderText(object sender, RoutedEventArgs e)
        {
            if (FileNameTextBox.Text == "Bestandsnaam")
            {
                FileNameTextBox.Text = "";
            }
        }

        private void RestorePlaceholderText(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(FileNameTextBox.Text))
            {
                FileNameTextBox.Text = "Bestandsnaam";
            }
        }

        private void MenuButton_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button)
            {
                string tag = button.Tag.ToString();

                if (tag == "Notities")
                {
                    StartPanel.Visibility = Visibility.Collapsed;
                    NotesPanel.Visibility = Visibility.Visible;
                    NotesList.Visibility = Visibility.Visible;
                    NoteTitleTextBox.Visibility = Visibility.Collapsed;
                    NoteContentTextBox.Visibility = Visibility.Collapsed;
                    SaveButton.Visibility = Visibility.Collapsed;
                    AddNewNoteButton.Visibility = Visibility.Visible;
                }
                else
                {
                    NotesPanel.Visibility = Visibility.Collapsed;
                    StartPanel.Visibility = Visibility.Visible;
                }
            }
        }

        private void NotesTitle_Click(object sender, MouseButtonEventArgs e)
        {
            NotesPanel.Visibility = Visibility.Collapsed;
            StartPanel.Visibility = Visibility.Visible;
        }

        private void NotesList_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (NotesList.SelectedItem is Note selectedNote)
            {
                ViewNote(selectedNote);
            }
        }

        private void DeleteNote_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.CommandParameter is Note noteToDelete)
            {
                Notes.Remove(noteToDelete);
                var filePath = Path.Combine(NotesDirectory, noteToDelete.Title);
                if (File.Exists(filePath))
                {
                    File.Delete(filePath);
                }
                MessageBox.Show("Notitie verwijderd!");
            }
        }

        private void ViewNote(Note note)
        {
            currentNote = note;
            NoteTitleTextBox.Text = note.Title;
            NoteContentTextBox.Text = note.Content;
            NoteTitleTextBox.IsReadOnly = true;
            NoteContentTextBox.IsReadOnly = true;

            AddNewNoteButton.Visibility = Visibility.Collapsed;
            NoteTitleTextBox.Visibility = Visibility.Visible;
            NoteContentTextBox.Visibility = Visibility.Visible;
            SaveButton.Visibility = Visibility.Collapsed;
            NotesList.Visibility = Visibility.Collapsed;
        }
    }
}
