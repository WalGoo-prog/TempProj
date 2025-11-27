using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerController_PhysX : MonoBehaviour
{
    private Rigidbody playerRB;
    public float force = 3.0f;
    private Vector2 moveInput;
    private void Start(){
        playerRB = GetComponent<Rigidbody>();
    }

    public void OnMove(InputValue value){
        moveInput = value.Get<Vector2>();
    }
    private void FixedUpdate(){
        Vector3 movement = new Vector3(moveInput.x, 0, moveInput.y);
        playerRB.AddForce(movement * force);
    }
}

