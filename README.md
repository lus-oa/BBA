# BBA

As the core of streaming media services, the ABR algorithm plays a role in adjusting the video download rate on the client side,

with the goal of selecting higher video rates and generating fewer playback stalling events.

An existing ABR algorithm, the BBA algorithm, proposes to use only buffer occupancy for video rate selection.

The algorithm divides the buffer into three areas and uses different rate selection mechanisms in different areas.

Experimental results show that the BBA algorithm performs well in terms of video rate and playback stalling rate, but there is still a significant gap compared to Netflix's default ABR algorithm. 

This paper analyzes and improves the BBA algorithm and proposes two improved algorithms, BBA-1 and BBA-2.

BBA-1 optimizes the overly conservative startup phase in BBA, uses variable bit rate (VBR) to calculate video chunk size, and increases video rate more quickly based on the buffer change rate.

This algorithm improves the average video rate by nearly 200kb/s compared to BBA, but the overly aggressive rate increase method also increases the playback stalling rate,

and the use of VBR encoding makes network bandwidth more sensitive and increases video switching frequency.

BBA-2 attempts to reduce the rate switching frequency by adding a simple network bandwidth estimation when selecting the video rate,

predicting future network bandwidth based on existing video segments in the buffer.

This algorithm can reduce the rate switching rate by nearly 50% while maintaining a similar average video rate to BBA-1.

Both of these improved algorithms can produce significant improvements for different goals and play a good role in improving user QoE.
