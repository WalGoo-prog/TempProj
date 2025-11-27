using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
public class PlayerController : MonoBehaviour
{
    public float speed = 10.0f;
    private Vector2 moveInput;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    public void OnMove(InputValue value)
    {
        moveInput = value.Get<Vector2>();
    }
    // Update is called once per frame
    void Update()
    {
        Vector3 movement = new Vector3(moveInput.x, 0, moveInput.y);
        transform.Translate(movement * speed * Time.deltaTime);
    }
}
