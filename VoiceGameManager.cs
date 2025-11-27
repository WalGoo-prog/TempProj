using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

public class VoiceGameManager : MonoBehaviour
{
    [Header("UI Groups")]
    public GameObject conversationUI;

    [Header("UI Elements")]
    public Button recordButton;
    public Button exitButton;
    public Text statusText;
    public Text npcSubtitleText;
    public Text feedbackText;
    public Text userSpeechText;

    [Header("Audio Settings")]
    public AudioSource npcAudioSource;

    public GameState currentGameState;
    private string backupGameStateJson;

    private AudioClip recordedClip;
    private string micName;
    private bool isRecording = false;
    private bool isProcessing = false;

    private const string SERVER_URL_INTERACT = "http://127.0.0.1:8000/interact";
    private const string SERVER_URL_START = "http://127.0.0.1:8000/start_conversation";

    void Start()
    {
        if (Microphone.devices.Length > 0)
        {
            micName = Microphone.devices[0];
            recordButton.onClick.AddListener(ToggleRecording);
            UpdateStatus("Exploration Mode");
        }
        else
        {
            UpdateStatus("No Microphone!");
            if (recordButton) recordButton.interactable = false;
        }

        if (exitButton) exitButton.onClick.AddListener(ExitHeritageMode);

        if (conversationUI != null) conversationUI.SetActive(false);
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;

        if (currentGameState == null || currentGameState.heritages == null || currentGameState.heritages.Count == 0)
        {
            StartNewGame("Player1", "Male", "Guide", "Female", autoStartConversation: false);
        }
    }

    // =========================================================
    // [1] 구역 진입 (재진입 방지 및 UI 켜기)
    // =========================================================
    public void EnterHeritageZone(string targetHeritageName)
    {
        if (currentGameState == null || currentGameState.heritages == null) return;

        int targetIndex = currentGameState.heritages.FindIndex(h => h.name == targetHeritageName);

        if (targetIndex == -1)
        {
            Debug.LogError($"[Error] Heritage '{targetHeritageName}' not found!");
            return;
        }

        // [핵심 1] 이미 완료된 곳이면 절대 시작하지 않음
        if (currentGameState.heritages[targetIndex].completed)
        {
            UpdateStatus($"{targetHeritageName} is already cleared!");
            Debug.Log($"{targetHeritageName} is done. Ignoring entry.");
            return;
        }

        // 진입 전 상태 백업
        backupGameStateJson = JsonUtility.ToJson(currentGameState);

        // 인덱스 강제 변경 (순서 상관없이 진입한 곳으로)
        Debug.Log($"[Action] Entering {targetHeritageName}...");
        currentGameState.current_index = targetIndex;
        currentGameState.retry_count = 0;

        // UI 켜기 & 커서 해제
        if (conversationUI != null) conversationUI.SetActive(true);
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;

        StopAllCoroutines();
        StartCoroutine(RequestOpeningConversation());
    }

    // 종료/취소
    public void ExitHeritageMode()
    {
        if (!string.IsNullOrEmpty(backupGameStateJson))
        {
            // 현재 설명 중이던 곳이 완료되지 않았다면 롤백
            int idx = currentGameState.current_index;
            if (idx < currentGameState.heritages.Count && !currentGameState.heritages[idx].completed)
            {
                currentGameState = JsonUtility.FromJson<GameState>(backupGameStateJson);
                Debug.Log("Exited without completion. Progress reset.");
            }
        }

        StopAllCoroutines();
        if (npcAudioSource.isPlaying) npcAudioSource.Stop();

        if (npcSubtitleText) npcSubtitleText.text = "";
        if (userSpeechText) userSpeechText.text = "";

        isProcessing = false;
        isRecording = false;

        if (conversationUI != null) conversationUI.SetActive(false);
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;

        UpdateStatus("Exploration Mode");
    }

    // =========================================================
    // [2] 응답 처리 (완료 판단 수정)
    // =========================================================
    void HandleServerResponse(string jsonString, byte[] sentWavData = null)
    {
        ServerResponse response = JsonUtility.FromJson<ServerResponse>(jsonString);

        if (response.updated_game_state != null)
        {
            // 이전 인덱스 기억 (완료 판단용)
            int prevIndex = currentGameState.current_index;

            GameState prevState = currentGameState;
            string slot = currentGameState.save_slot_name;
            currentGameState = response.updated_game_state;
            if (string.IsNullOrEmpty(currentGameState.save_slot_name)) currentGameState.save_slot_name = slot;

            // [핵심 2] 완료 판단 로직 수정
            // 조건 A: 인덱스가 다음으로 넘어갔음 (서버가 완료 후 넘김)
            // 조건 B: 방금 설명하던 인덱스의 completed가 true임
            bool isHeritageFinished = false;

            if (currentGameState.current_index > prevIndex)
            {
                // 인덱스가 넘어갔다는 건 이전 문화재가 끝났다는 뜻
                isHeritageFinished = true;
            }
            else if (prevIndex < currentGameState.heritages.Count && currentGameState.heritages[prevIndex].completed)
            {
                // 인덱스는 그대로지만 완료 플래그가 켜짐
                isHeritageFinished = true;
            }

            CheckAndSaveProgress(prevState, currentGameState);

            if (isHeritageFinished)
            {
                Debug.Log("Heritage Completed! Closing UI...");

                // 완료되었으므로 백업 갱신 (취소해도 완료 상태 유지)
                backupGameStateJson = JsonUtility.ToJson(currentGameState);

                // 멘트 재생 후 자동 종료
                StartCoroutine(WaitAndCloseUI(response.audio_base64));
            }
            else
            {
                // 계속 진행 중이면 즉시 재생
                if (!string.IsNullOrEmpty(response.audio_base64))
                    StartCoroutine(PlayBase64Audio(response.audio_base64));
            }

            // 피드백 저장
            if (!string.IsNullOrEmpty(response.feedback) && !string.IsNullOrEmpty(response.user_stt))
            {
                string hName = GetCurrentHeritageName();
                SaveManager.AppendFeedback(currentGameState.save_slot_name, hName, response.user_stt, response.feedback);
            }
        }

        // 녹음 저장
        if (sentWavData != null && !string.IsNullOrEmpty(response.user_stt))
        {
            string hName = GetCurrentHeritageName();
            SaveManager.SaveUserRecording(currentGameState.save_slot_name, hName, "Voice", sentWavData);
        }

        // UI 텍스트 표시
        if (npcSubtitleText) npcSubtitleText.text = response.npc_response;
        if (userSpeechText && !string.IsNullOrEmpty(response.user_stt)) userSpeechText.text = $"You: {response.user_stt}";

        if (!string.IsNullOrEmpty(response.user_stt))
            UpdateStatus($"Score: {response.pronunciation_score:F0}");
        else
            UpdateStatus("Listening...");
    }

    IEnumerator WaitAndCloseUI(string audioBase64)
    {
        // 마지막 멘트 재생
        if (!string.IsNullOrEmpty(audioBase64))
        {
            yield return StartCoroutine(PlayBase64Audio(audioBase64));
        }

        // 오디오 끝날 때까지 대기
        if (npcAudioSource.clip != null)
        {
            yield return new WaitForSeconds(npcAudioSource.clip.length + 1.0f);
        }

        // UI 닫기
        ExitHeritageMode();
    }

    // ... (기존 함수들 유지: StartNewGame, LoadGame, InitializeQuestData 등) ...
    public void StartNewGame(string pName, string pGender, string nName, string nGender, bool autoStartConversation = false)
    {
        currentGameState = new GameState();
        currentGameState.player_info = new PersonaInfo(pName, pGender);
        currentGameState.npc_info = new PersonaInfo(nName, nGender);
        currentGameState.save_slot_name = $"Save_{pName}_{DateTime.Now:MMdd_HHmm}";
        InitializeQuestData();
        SaveManager.SaveGame(currentGameState);
        if (autoStartConversation) StartCoroutine(RequestOpeningConversation());
    }

    public void LoadGame(string saveSlotName) { /* 기존 코드 */ }

    void InitializeQuestData()
    {
        currentGameState.heritages = new List<HeritageStatus>();
        currentGameState.current_index = 0;
        currentGameState.retry_count = 0;

        // 1. GwangHwaMoon
        var h1 = new HeritageStatus { name = "GwangHwaMoon", completed = false };
        h1.keywords = new List<KeywordStatus> {
            new KeywordStatus { keyword = "1395", sample_question = "When was this built?", isDone = false },
            new KeywordStatus { keyword = "King Taejo", sample_question = "Who built this?", isDone = false }
        };
        currentGameState.heritages.Add(h1);

        // 2. GyeongHeoiRu (이게 다음 문화재)
        var h2 = new HeritageStatus { name = "GyeongHeoiRu", completed = false };
        h2.keywords = new List<KeywordStatus> {
            new KeywordStatus { keyword = "Banquet", sample_question = "What was this building used for?", isDone = false },
            new KeywordStatus { keyword = "Artificial Pond", sample_question = "What feature surrounds this building?", isDone = false }
        };
        currentGameState.heritages.Add(h2);

        // 3. JoseonTongShinSaSeon
        var h3 = new HeritageStatus { name = "JoseonTongShinSaSeon", completed = false };
        h3.keywords = new List<KeywordStatus> {
            new KeywordStatus { keyword = "1695", sample_question = "When was this ship used?", isDone = false }
        };
        currentGameState.heritages.Add(h3);

        // 4. SoSwaeWon
        var h4 = new HeritageStatus { name = "SoSwaeWon", completed = false };
        h4.keywords = new List<KeywordStatus> {
            new KeywordStatus { keyword = "1695", sample_question = "When was this garden built?", isDone = false }
        };
        currentGameState.heritages.Add(h4);

        // 5. NakAnEupSeong
        var h5 = new HeritageStatus { name = "NakAnEupSeong", completed = false };
        h5.keywords = new List<KeywordStatus> {
            new KeywordStatus { keyword = "1695", sample_question = "When was this fortress constructed?", isDone = false }
        };
        currentGameState.heritages.Add(h5);
    }

    IEnumerator RequestOpeningConversation()
    {
        UpdateStatus("NPC is thinking...");
        if (npcSubtitleText) npcSubtitleText.text = "...";
        string jsonState = JsonUtility.ToJson(currentGameState);
        WWWForm form = new WWWForm();
        form.AddField("request_data", jsonState);
        using (UnityWebRequest www = UnityWebRequest.Post(SERVER_URL_START, form))
        {
            yield return www.SendWebRequest();
            if (www.result == UnityWebRequest.Result.Success) HandleServerResponse(www.downloadHandler.text);
            else Debug.LogError(www.error);
        }
    }

    IEnumerator SendAudioToServer(AudioClip clip)
    {
        isProcessing = true;
        byte[] wavData = WavUtility.FromAudioClip(clip);
        string jsonState = JsonUtility.ToJson(currentGameState);
        WWWForm form = new WWWForm();
        form.AddBinaryData("audio_file", wavData, "user_input.wav", "audio/wav");
        form.AddField("request_data", jsonState);
        using (UnityWebRequest www = UnityWebRequest.Post(SERVER_URL_INTERACT, form))
        {
            yield return www.SendWebRequest();
            if (www.result == UnityWebRequest.Result.Success) HandleServerResponse(www.downloadHandler.text, wavData);
            else Debug.LogError(www.error);
        }
        isProcessing = false;
    }

    string GetCurrentHeritageName()
    {
        if (currentGameState.heritages != null && currentGameState.current_index < currentGameState.heritages.Count)
            return currentGameState.heritages[currentGameState.current_index].name;
        return "Unknown";
    }

    void CheckAndSaveProgress(GameState oldState, GameState newState)
    {
        bool needSave = false;
        int idx = newState.current_index;
        if (newState.current_index > oldState.current_index) needSave = true;
        else if (idx < newState.heritages.Count && newState.heritages[idx].completed) needSave = true;
        if (needSave) SaveManager.SaveGame(newState);
    }

    void ToggleRecording() { if (!isRecording) StartRecording(); else StopRecordingAndSend(); }
    void StartRecording() { isRecording = true; recordedClip = Microphone.Start(micName, false, 10, 44100); UpdateStatus("Recording..."); }
    void StopRecordingAndSend() { if (!isRecording) return; isRecording = false; Microphone.End(micName); UpdateStatus("Sending..."); StartCoroutine(SendAudioToServer(recordedClip)); }
    IEnumerator PlayBase64Audio(string base64String)
    {
        byte[] audioBytes = Convert.FromBase64String(base64String);
        string tempPath = Path.Combine(Application.persistentDataPath, "npc_response.mp3");
        File.WriteAllBytes(tempPath, audioBytes);
        using (UnityWebRequest www = UnityWebRequestMultimedia.GetAudioClip("file://" + tempPath, AudioType.MPEG))
        {
            yield return www.SendWebRequest();
            if (www.result == UnityWebRequest.Result.Success) { AudioClip clip = DownloadHandlerAudioClip.GetContent(www); npcAudioSource.clip = clip; npcAudioSource.Play(); }
        }
    }
    void UpdateStatus(string msg) { if (statusText) statusText.text = msg; }
    void OnApplicationQuit() { if (currentGameState != null) SaveManager.SaveGame(currentGameState); }
}