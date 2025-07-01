; Alternative 4-Portal Farming Cycle (60s)
; Usage: X(1), R(1), C(4), G(2), D(liberal)
; Route: BL → TL → TR → BR → BL (40-50s combat at TR)

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
AlternativeFarmingCycle:
Loop
{
    ; Phase 1: Setup - R Clone Deployment (Bottom Left) - 3s
    ; Starting at Bottom Left Portal
    Send, {r Down}
    Sleep, 100
    Send, {r Up}
    Sleep, 100
    
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 300
    
    ; Phase 2: Setup - X Clone Deployment (Top Left) - 4s
    ; Now at Top Left Portal
    Sleep, 100
    
    Send, {Down Down}
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Send, {Down Up}
    Sleep, 500
    
    Sleep, 100
    
    Send, {x Down}
    Sleep, 100
    Send, {x Up}
    Sleep, 100
    
    Send, {End}
    Sleep, 1000
    
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 300
    
    ; Phase 3: Manual Combat Phase (Top Right) - 45s
    ; Now at Top Right Portal
    Sleep, 100
    
    Send, {Down Down}
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Send, {Down Up}
    Sleep, 400
    
    ; Extended Combat Phase (6 spawn cycles × 7s = 42s + 3s buffer)
    ; Spawn Cycle 1 (7s) - Time: 7s-14s
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 800
    
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 1200
    
    Send, {d Down}
    Sleep, 100
    Send, {d Up}
    Sleep, 3400
    
    ; Spawn Cycle 2 (7s) - Time: 14s-21s
    Send, {g Down}
    Sleep, 100
    Send, {g Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1700
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 1200
    
    Send, {d Down}
    Sleep, 100
    Send, {d Up}
    Sleep, 3500
    
    ; Spawn Cycle 3 (7s) - Time: 21s-28s
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 300
    Send, {d Up}
    Sleep, 1500
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1000
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 3600
    
    ; Spawn Cycle 4 (7s) - Time: 28s-35s
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1800
    
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1000
    
    Send, {d Down}
    Sleep, 100
    Send, {d Up}
    Sleep, 3500
    
    ; Spawn Cycle 5 (7s) - Time: 35s-42s
    Send, {g Down}
    Sleep, 100
    Send, {g Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 300
    Send, {d Up}
    Sleep, 1500
    
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1200
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 3400
    
    ; Spawn Cycle 6 (7s) - Time: 42s-49s
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1700
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 1000
    
    Send, {d Down}
    Sleep, 100
    Send, {d Up}
    Sleep, 3800
    
    ; Buffer time (Time: 49s-52s)
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1500
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 1000
    
    ; Phase 4: Return Route (Top Right → Bottom Right → Bottom Left) - 8s
    Send, {End}
    Sleep, 1000
    
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 300
    
    Sleep, 100
    
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 300
    
    Sleep, 100
}
Return