using UnityEngine;

public class HeritageTrigger : MonoBehaviour
{
    [Header("설정")]
    // Unity 에디터에서 JSON 데이터의 이름(예: GwangHwaMoon)과 똑같이 적어야 합니다.
    public string heritageName;

    private VoiceGameManager gameManager;

    void Start()
    {
        gameManager = FindObjectOfType<VoiceGameManager>();
    }

    // 구역 진입 시: 설명 시작
    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Player"))
        {
            Debug.Log($"[Trigger] Entered {heritageName}");
            gameManager.EnterHeritageZone(heritageName);
        }
    }

    // 구역 이탈 시: 설명 취소 및 UI 숨김
    private void OnTriggerExit(Collider other)
    {
        if (other.CompareTag("Player"))
        {
            Debug.Log($"[Trigger] Exited {heritageName}");
            gameManager.ExitHeritageMode();
        }
    }
}