using System.IO;
using UnityEngine;
using System.Collections.Generic;
using System.Linq;

public static class SaveManager
{
    // 프로젝트 루트 경로 (Assets 폴더의 상위 폴더)
    private static string ProjectRoot => Directory.GetParent(Application.dataPath).FullName;

    // 세이브 메인 폴더: [ProjectRoot]/Saves
    private static string RootSavePath => Path.Combine(ProjectRoot, "Saves");

    static SaveManager()
    {
        // Saves 폴더가 없으면 생성
        if (!Directory.Exists(RootSavePath)) Directory.CreateDirectory(RootSavePath);
    }

    // =========================================================
    // [1] 게임 상태 저장 및 로드 (JSON)
    // =========================================================

    public static void SaveGame(GameState state)
    {
        if (string.IsNullOrEmpty(state.save_slot_name))
            state.save_slot_name = $"Save_{System.DateTime.Now:yyyyMMdd_HHmmss}";

        state.last_updated = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

        // 경로: Saves/[SlotName]/GameData.json
        string slotFolderPath = Path.Combine(RootSavePath, state.save_slot_name);
        if (!Directory.Exists(slotFolderPath)) Directory.CreateDirectory(slotFolderPath);

        string json = JsonUtility.ToJson(state, true);
        string filePath = Path.Combine(slotFolderPath, "GameData.json");

        File.WriteAllText(filePath, json);
        Debug.Log($"[SaveManager] Game Saved: {filePath}");
    }

    public static GameState LoadGame(string slotName)
    {
        string filePath = Path.Combine(RootSavePath, slotName, "GameData.json");

        if (File.Exists(filePath))
        {
            string json = File.ReadAllText(filePath);
            GameState state = JsonUtility.FromJson<GameState>(json);
            state.save_slot_name = slotName;
            Debug.Log($"[SaveManager] Game Loaded: {slotName}");
            return state;
        }
        else
        {
            Debug.LogError($"[SaveManager] Save file not found: {filePath}");
            return null;
        }
    }

    // =========================================================
    // [2] 피드백 저장 (TXT)
    // =========================================================

    public static void AppendFeedback(string slotName, string heritageName, string userText, string feedbackContent)
    {
        if (string.IsNullOrEmpty(slotName)) return;

        string slotFolderPath = Path.Combine(RootSavePath, slotName);
        string feedbackDir = Path.Combine(slotFolderPath, "Feedbacks");

        if (!Directory.Exists(feedbackDir)) Directory.CreateDirectory(feedbackDir);

        string fileName = $"{heritageName}_Feedback.txt";
        string filePath = Path.Combine(feedbackDir, fileName);

        string timeStamp = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        string logContent = $"[{timeStamp}]\n" +
                            $"User Said: \"{userText}\"\n" +
                            $"Feedback: {feedbackContent}\n" +
                            $"--------------------------------------------------\n";

        try
        {
            File.AppendAllText(filePath, logContent);
            Debug.Log($"[SaveManager] Feedback appended to: {filePath}");
        }
        catch (System.Exception e)
        {
            Debug.LogError($"[SaveManager] Failed to write feedback: {e.Message}");
        }
    }

    // =========================================================
    // [3] 녹음 파일 저장 (WAV)
    // =========================================================

    public static void SaveUserRecording(string slotName, string heritageName, string keyword, byte[] wavData)
    {
        if (string.IsNullOrEmpty(slotName)) return;

        // 경로: Saves/[SlotName]/Feedbacks/Records/
        string feedbackDir = Path.Combine(RootSavePath, slotName, "Feedbacks");
        string recordDir = Path.Combine(feedbackDir, "Records");

        if (!Directory.Exists(recordDir)) Directory.CreateDirectory(recordDir);

        // 파일명 생성 (중복 방지)
        int count = 1;
        // 파일명에 특수문자가 포함되지 않도록 간단히 정제
        string safeKeyword = new string(keyword.Where(char.IsLetterOrDigit).ToArray());
        string fileName = $"{heritageName}_{safeKeyword}_{count}.wav";
        string filePath = Path.Combine(recordDir, fileName);

        while (File.Exists(filePath))
        {
            count++;
            fileName = $"{heritageName}_{safeKeyword}_{count}.wav";
            filePath = Path.Combine(recordDir, fileName);
        }

        try
        {
            File.WriteAllBytes(filePath, wavData);
            Debug.Log($"[SaveManager] Recording saved: {fileName}");
        }
        catch (System.Exception e)
        {
            Debug.LogError($"[SaveManager] Failed to save recording: {e.Message}");
        }
    }

    // =========================================================
    // [4] 유틸리티
    // =========================================================

    public static List<string> GetAllSaveSlots()
    {
        if (!Directory.Exists(RootSavePath)) return new List<string>();

        return Directory.GetDirectories(RootSavePath)
                        .Select(Path.GetFileName)
                        .ToList();
    }
}