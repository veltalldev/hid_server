; Fixed 4-Portal Farming Cycle (60s)
; Usage: X(1), R(1), C(4), G(2), D(liberal)
; Route: TR → BR → TL → setup clones → move left → BL → TR → manual combat

#NoEnv
SetWorkingDir %A_ScriptDir%
CoordMode, Mouse, Window
SendMode Input
#SingleInstance Force
SetTitleMatchMode 2
#WinActivateForce
SetControlDelay 1
SetWinDelay 0
SetKeyDelay -1
SetMouseDelay -1
SetBatchLines -1


F5::
Macro3:
Loop
{
    ; Phase 1: Initial Clear & Portal Route (Top Right) - 4s
    ; Starting at Top Right Portal
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 600
    
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 600
    
    ; Now at Bottom Right Portal
    Sleep, 300
    
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 600
    
    ; Phase 2: Clone Setup (Top Left) - 8s
    ; Now at Top Left Portal
    Sleep, 300
    
    ; Jump down once for X clone
    Send, {Down Down}
    Sleep, 50
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Sleep, 50
    Send, {Down Up}
    Sleep, 500
    
    Sleep, 100
    
    Send, {x Down}
    Sleep, 100
    Send, {x Up}
    Sleep, 1600
    
    ; Jump down twice more for R clone
    Send, {Down Down}
    Sleep, 50
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Sleep, 50
    Send, {Down Up}
    Sleep, 600
    
    Sleep, 100
    
    Send, {Down Down}
    Sleep, 50
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Sleep, 50
    Send, {Down Up}
    Sleep, 600
    
    Sleep, 100
    
    Send, {r Down}
    Sleep, 100
    Send, {r Up}
    Sleep, 600
    
    ; Phase 3: Move Left to Bottom Left Portal - 2s
    Send, {Left Down}
    Sleep, 100
    Send, {Left Up}
    Sleep, 100
    
    ; Should now be at Bottom Left Portal
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 300
    
    ; Phase 4: Second Clear & Setup Combat (Top Right) - 3s
    ; Now back at Top Right Portal
    Sleep, 100
    
    ; Jump down twice for combat position
    Send, {Down Down}
    Sleep, 50
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Sleep, 50
    Send, {Down Up}
    Sleep, 600
    
    Sleep, 100
    
    Send, {Down Down}
    Sleep, 50
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Sleep, 50
    Send, {Down Up}
    Sleep, 600
    
    ; Phase 5: Extended Manual Combat - 43s
    ; Combat Phase (6 spawn cycles × 7s = 42s + 1s buffer)
    
    ; Spawn Cycle 1 (7s) - Time: 17s-24s

    
    Send, {g Down}
    Sleep, 100
    Send, {g Up}
    Sleep, 600
    
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 600
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1000
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 1200
    
    Send, {d Down}
    Sleep, 100
    Send, {d Up}
    Sleep, 4200

    
    ; Spawn Cycle 2 (7s) - Time: 24s-31s
    
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1500
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1000
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 3700
    
    ; Spawn Cycle 3 (7s) - Time: 31s-38s
    Send, {d Down}
    Sleep, 300
    Send, {d Up}
    Sleep, 1800
    
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1200
    
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 3200

    
    ; Spawn Cycle 4 (7s) - Time: 38s-45s
    Send, {g Down}
    Sleep, 100
    Send, {g Up}
    Sleep, 600
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1500
    
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1000
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 3700

    Send, {d Down}
    Sleep, 300
    Send, {d Up}
    Sleep, 1800
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1200
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 3300
    
    ; Spawn Cycle 6 (7s) - Time: 52s-59s
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1500
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1000
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 4000

    ; Phase 6: Return to Start - 2s because long way up for this setup
    Send, {End Down}
    Sleep, 200
    Send, {End Up}
    Sleep, 2000
    
    ; Should land back at Top Right Portal ready for next cycle
}
Return