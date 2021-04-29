layout = """
0.0	enable	BOOL	# Enable camera
0.1	scan	BOOL	# Part position request
2.0 ready   BOOL    # Camera is ready
2.1 busy    BOOL    # Camera is busy
2.2 done    BOOL    # Part position calculated
2.3 reserve2    BOOL   # reserve
2.4 reserve3    BOOL   # reserve
2.5 reserve4    BOOL   # reserve
2.6 reserve5    BOOL   # reserve
2.7 watchdog    BOOL   # Watchdog
4.0 camera1 BOOL    # camera 1 connection error
4.1 camera2 BOOL    # camera 2 connection error
6 coordinateX   REAL   # Part X coordinate
10 coordinateY   REAL   # Part Y coordinate
"""
