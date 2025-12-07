--- START OF FILE ohcha_shape_utils.txt ---

/*
================================================================================
  Project:      ohCHA Rig Manager - Shape Utilities
  Description:  [v0.90_Beta] SHAPE GENERATION FULL CODE.
                - INTEGRITY: Full code, no omissions.
                - FIXED: createCurveController uses explicit construction.
================================================================================
*/

print ">>> [DEBUG] Loading 'ohcha_shape_utils.txt'..."
try ( global ohCHA_ShapeUtils = undefined ) catch()
gc light:true

struct OhchaShapeUtils_Struct
(
    -- [1] Pin Shape (Based on user-provided data)
    fn createPinShape size =
    (
        local s = SplineShape()
        s.name = uniqueName "Ctrl_Pin_"
        s.wirecolor = yellow
        addNewSpline s

        local f = size / 10.0

        addKnot s 1 #bezier #curve ([0, 5.161, 0]*f) ([0, 5.161, 1.290]*f) ([0, 5.161, -1.290]*f)
        addKnot s 1 #bezier #curve ([0, 7.5, -2.338]*f) ([0, 6.209, -2.338]*f) ([0, 8.790, -2.338]*f)
        addKnot s 1 #bezier #curve ([0, 9.838, 0]*f) ([0, 9.838, -1.290]*f) ([0, 9.838, 1.290]*f)
        addKnot s 1 #bezier #curve ([0, 7.5, 2.338]*f) ([0, 8.790, 2.338]*f) ([0, 6.209, 2.338]*f)
        addKnot s 1 #bezierCorner #curve ([0, 5.161, 0]*f) ([0, 5.161, 1.290]*f) ([0, 3.450, 0]*f)
        addKnot s 1 #corner #line ([0, 0, 0]*f) ([0, 1.725, 0]*f) ([0, 0, 0]*f)

        updateShape s
        
        -- Alignment: Rotate X 90 (Align to Z-Up)
        rotate s (angleaxis 90 [1,0,0])
        
        resetXForm s
        convertToSplineShape s 

        return s
    ),

    -- [2] Generic Controllers
    fn createCurveController typeName size =
    (
        print (">>> [ShapeUtils] Creating Controller: " + typeName)
        
        undo "Create Controller" on (
            local shp = undefined
            
            if typeName == "Pin" then (
                shp = this.createPinShape size
            )
            else if typeName == "Circle" then (
                -- Explicit Circle Creation
                local tempCircle = Circle radius:size
                tempCircle.name = uniqueName "Ctrl_Circle_"
                tempCircle.wirecolor = yellow
                convertToSplineShape tempCircle
                shp = tempCircle
            )
            else if typeName == "Box" then (
                -- Explicit Box Creation (Wireframe)
                shp = SplineShape()
                shp.name = uniqueName "Ctrl_Box_"
                shp.wirecolor = yellow
                
                local s = size
                
                -- 1. Top Square (Z+)
                addNewSpline shp
                addKnot shp 1 #corner #line [s,s,s]
                addKnot shp 1 #corner #line [s,-s,s]
                addKnot shp 1 #corner #line [-s,-s,s]
                addKnot shp 1 #corner #line [-s,s,s]
                close shp 1
                
                -- 2. Bottom Square (Z-)
                addNewSpline shp
                addKnot shp 2 #corner #line [s,s,-s]
                addKnot shp 2 #corner #line [s,-s,-s]
                addKnot shp 2 #corner #line [-s,-s,-s]
                addKnot shp 2 #corner #line [-s,s,-s]
                close shp 2
                
                -- 3. Vertical Pillars
                -- Line 1
                addNewSpline shp
                addKnot shp 3 #corner #line [s,s,s]
                addKnot shp 3 #corner #line [s,s,-s]
                
                -- Line 2
                addNewSpline shp
                addKnot shp 4 #corner #line [s,-s,s]
                addKnot shp 4 #corner #line [s,-s,-s]
                
                -- Line 3
                addNewSpline shp
                addKnot shp 5 #corner #line [-s,-s,s]
                addKnot shp 5 #corner #line [-s,-s,-s]
                
                -- Line 4
                addNewSpline shp
                addKnot shp 6 #corner #line [-s,s,s]
                addKnot shp 6 #corner #line [-s,s,-s]
                
                updateShape shp
            )
            
            -- [Auto Align] If objects are selected, match position to the first one
            if (isValidNode shp) and (selection.count > 0) do (
                shp.transform = selection[1].transform
                print ("    -> Aligned to: " + selection[1].name)
            )
            
            if (isValidNode shp) do select shp
            
            if (isValidNode shp) then (
                print ("    ✅ Created: " + shp.name)
                return shp
            ) else (
                print "    ❌ Failed to create shape."
                return undefined
            )
        )
    )
)
global ohCHA_ShapeUtils = OhchaShapeUtils_Struct()
print "✅ [Module] ShapeUtils Loaded (v0.90 Full)."