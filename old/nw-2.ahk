; Optimized 4-Portal Farming Cycle (60s)
; Usage: X(1), R(1), C(4), G(2), D(liberal)
; Route: TR → Central-R → BR → BL → TL → Central-L (48s combat)

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
OptimizedFarmingCycle:
Loop
{
    ; Phase 1: Setup - X Clone Deployment (Central-Right) - 4s
    ; Starting at Top Right Portal
    Send, {Down Down}
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Send, {Down Up}
    Sleep, 300
    
    Sleep, 100
    
    Send, {Down Down}
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Send, {Down Up}
    Sleep, 400
    
    Sleep, 100
    
    Send, {x Down}
    Sleep, 100
    Send, {x Up}
    Sleep, 100
    
    Send, {End}
    Sleep, 1400
    
    ; Phase 2: Setup - R Clone Deployment (Bottom Right) - 3s
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 300
    
    Sleep, 100
    
    Send, {r Down}
    Sleep, 100
    Send, {r Up}
    Sleep, 100
    
    Send, {g Down}
    Sleep, 100
    Send, {g Up}
    Sleep, 100
    
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 200
    
    ; Phase 3: Setup - Quick AoE Clear (Bottom Left) - 3s
    Sleep, 100
    
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 100
    
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 300
    
    Sleep, 100
    
    Send, {Down Down}
    Send, {Space Down}
    Sleep, 50
    Send, {Space Up}
    Send, {Down Up}
    Sleep, 300
    
    ; Phase 4: Manual Combat (Central-Left) - 48s
    ; Spawn Cycle 1 (7s) - Time: 10s-17s
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 800
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 1200
    
    Send, {d Down}
    Sleep, 100
    Send, {d Up}
    Sleep, 3600
    
    ; Spawn Cycle 2 (7s) - Time: 17s-24s
    Sleep, 100
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1700
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 4200
    
    ; Spawn Cycle 3 (7s) - Time: 24s-31s
    Send, {d Down}
    Sleep, 300
    Send, {d Up}
    Sleep, 1200
    
    Sleep, 100
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 4500
    
    ; Spawn Cycle 4 (7s) - Time: 31s-38s
    Sleep, 100
    Send, {g Down}
    Sleep, 100
    Send, {g Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1700
    
    Send, {d Down}
    Sleep, 100
    Send, {d Up}
    Sleep, 4200
    
    ; Spawn Cycle 5 (7s) - Time: 38s-45s
    Sleep, 100
    Send, {c Down}
    Sleep, 100
    Send, {c Up}
    Sleep, 100
    
    Send, {d Down}
    Sleep, 300
    Send, {d Up}
    Sleep, 1200
    
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 4500
    
    ; Spawn Cycle 6 (7s) - Time: 45s-52s
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 1700
    
    Send, {d Down}
    Sleep, 250
    Send, {d Up}
    Sleep, 1200
    
    Send, {d Down}
    Sleep, 100
    Send, {d Up}
    Sleep, 2700
    
    ; Buffer cycle if needed (Time: 52s-58s)
    Send, {d Down}
    Sleep, 150
    Send, {d Up}
    Sleep, 800
    
    Send, {d Down}
    Sleep, 200
    Send, {d Up}
    Sleep, 4200
    
    ; Phase 5: Return to Start (Top Right) - 2s
    Send, {End}
    Sleep, 1000
    
    Send, {Up Down}
    Sleep, 100
    Send, {Up Up}
    Sleep, 300
}
Return