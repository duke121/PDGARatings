# PDGA Ratings History per State
This project generates csv files that can be used in flourish to create a chart race to visualize the top players over the past 25 years in a state.

# How to run
1. 
In getPlayers.py, change the state, gender, etc. values to your liking and run
```
python getPlayers.py```

This can take up to an hour depending on your internet speed.

2. 
Then in fixData.py change the input file name to match the .csv file you just generated and run fixData.py
```
python fixData.py```

Your formatted file will have the filename + _decayed

3. 
Visualize the dataset by using my template in Flourish and replacing the data with your own, or some other data vis resource.
My example: https://public.flourish.studio/visualisation/27810199/


# Things to change
1. Move away from flourish and implement custom visulization tool, currently limited customziation
