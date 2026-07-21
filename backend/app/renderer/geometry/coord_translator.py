class CoordTranslator:
    EMU_PER_POINT = 12700
    EMU_PER_PIXEL = 9525 # 96 DPI
    
    @staticmethod
    def px_to_emu(pixels: float) -> int:
        return int(pixels * CoordTranslator.EMU_PER_PIXEL)
        
    @staticmethod
    def pt_to_emu(points: float) -> int:
        return int(points * CoordTranslator.EMU_PER_POINT)
