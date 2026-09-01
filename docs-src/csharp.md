---
title: C# and Unity SDK
anchor: docs-sdk-csharp
summary: Integrating the SDK into a Unity or C# simulation: initialisation, timekeeping, stage restarts, scoring and pass conditions.
status: published
note: The code examples carried three defects in the original documentation and have been repaired here, each marked with a corrected comment. The fixes are a field name, an Android intent variable name, and a stray semicolon that turned an initialisation guard into a no-op. Verify against your own build before relying on them.
---

## C# Unity Read Me Documentation

### Background

This is document is used to help developers integrate Febris functionality into XR simulations built in unity or with C#. Some of the sections posted pertain directly to Unity.

**Please keep in mind this library is a continuous work in progress and may change as well as these documents.**

### External Requirements

A few things are not provided that are needed to use this library properly. These items are:

1. Stopwatch instance (or timespan but the stopwatch is the most simple)
2. String array
3. float for score (Min, Max, Raw, and Scaled)
4. Newtonsoft.Json dll that is at least 12.0.0.0

The stopwatch instance is used for keeping track of how long a user is in a simulation. This will be used multiple times.

The string array will be used to collect Command line arguments.

Example:

```csharp
public class testScript : MonoBehaviour
{
    Stopwatch __stopwatch = new Stopwatch();
    float __rawScore = 0f;
    float __minScore = 0f;
    float __maxScore = 100f;
    float __scaledScore = 0f;

    void Start()
    {
        __stopwatch.Start();   // corrected: the field is __stopwatch
        string[] arguments = Environment.GetCommandLineArgs();
    }
}
```

### Adding the Febris dll

Add the febris dll (dynamic link library) to a folder in your project. This dll will be provided by Febris. It does not need to be stored in a specific location but it will need to be present. The namespace path can be seen below.

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement
```

### Initialization

Initialization needs to happen when the simulation starts. This will require the arguments to be passed into the newly initialized Febris files.

Example:

> Note: this snippet was reconstructed from damaged source. The brace nesting near the end of `Start()` is unbalanced in the original (an extra closing brace followed by a second `catch` block, and no closing brace for the class). The original text is kept as written rather than repaired.

```csharp
public class testScript : MonoBehaviour
{
    Stopwatch __stopwatch = new Stopwatch();
    float __rawScore = 0f;
    float __minScore = 0f;
    float __maxScore = 100f;
    float __scaledScore = 0f;
    float __period = 10f;
    float __nextUpdate = 10f;

    void Start()
    {
        __stopwatch.Start();

        bool isInitialized = false;

        string[] argumentArray = default;
        string[,] statementOutputArray = default;

        switch (Application.platform)
        {
            case RuntimePlatform.Android:
            {
                AndroidJavaClass UnityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer");
                AndroidJavaObject currentActivity = UnityPlayer.GetStatic<AndroidJavaObject>("currentActivity");
                AndroidJavaObject inputIntent = currentActivity.Call<AndroidJavaObject>(AndroidIntentConst.GetIntentTag);
                bool hasExtra = inputIntent.Call<bool>(AndroidIntentConst.HasExtrasTag, AndroidIntentConst.ArgumentExtraTag);
                if (!hasExtra) {
                    UnityEngine.Debug.Log("*********************Intent has no extras******************************");
                }

                AndroidJavaObject extras = inputIntent.Call<AndroidJavaObject>("getExtras");
                try {
                    string arguments = extras.Call<string>(AndroidIntentConst.GetStringTag, AndroidIntentConst.ArgumentExtraTag);
                    argumentArray = new string[] { arguments };
                    UnityEngine.Debug.Log(argumentArray);
                }
                catch {
                    UnityEngine.Debug.Log("*********************FAILED TO GET ARGUMENTS******************************");
                }
                break;
            }

            case RuntimePlatform.WindowsPlayer:
            {
                argumentArray = Environment.GetCommandLineArgs();
                break;
            }

            default:
            {
                Application.Quit();
                break;
            }
        }

        try {
            switch (Application.platform)
            {
                case RuntimePlatform.WindowsPlayer:
                {
                    (isInitialized, statementOutputArray) = Initializer.Initialize(argumentArray, ExpectedOperatingSystem.WindowsPC).Result;
                    break;
                }

                case RuntimePlatform.Android:
                {
                    (isInitialized, statementOutputArray) = Initializer.Initialize(argumentArray, ExpectedOperatingSystem.Android).Result;
                    Android_SendBroadcast(statementOutputArray, AndroidIntentConst.StatementCreation);
                    break;
                }

                case RuntimePlatform.IPhonePlayer:
                {
                    (isInitialized, statementOutputArray) = Initializer.Initialize(argumentArray, ExpectedOperatingSystem.iOSvariant).Result;
                    break;
                }
            }
        }
        catch (Exception ex) {
            Console.WriteLine("Error initalizing in Unity: " + ex.Message);
            throw;
        }

        string startpath = Application.persistentDataPath;

        UnityEngine.Debug.Log("isInitalized:" + isInitialized.ToString());

        if (!isInitialized)   // corrected: the original had a trailing semicolon here, which
                              // made the guard a no-op and quit the app on every successful start
        {
            UnityEngine.Debug.LogError("has not been initalized");
            #if (!UNITY_EDITOR)
            Application.Quit();
            #endif
        }

        new WaitForSeconds(1f);

        try {
            StatementHandler.UpdateStatement(XAPIProperties.Result, ResultOptions.ScoreMin, __minScore);
            StatementHandler.UpdateStatement(XAPIProperties.Result, ResultOptions.ScoreMax, __maxScore);

            switch (Application.platform)
            {
                case RuntimePlatform.WindowsPlayer:
                {
                    ///Nothing is need here for updates because windowsPlayer uses the file system.
                    break;
                }

                case RuntimePlatform.Android:
                {
                    (isInitialized, statementOutputArray) = StatementHandler.GetSendableUpdate().Result;
                    UnityEngine.Debug.Log("statement Output Array:" + statementOutputArray.ToString());
                    Android_SendBroadcast(statementOutputArray, AndroidIntentConst.StatementUpdate);
                    break;
                }

                case RuntimePlatform.IPhonePlayer:
                {
                    (isInitialized, statementOutputArray) = StatementHandler.GetSendableUpdate().Result;
                    break;
                }
            }
        }
        catch (Exception ex) {
            Console.WriteLine("Error updating statement in Unity: " + ex.Message);
            throw;
        }
        }
        catch (Exception ex) {
            UnityEngine.Debug.Log(ex.Message);
            UnityEngine.Debug.Log(ex.Data);
            #if (!UNITY_EDITOR)
            Application.Quit();
            #endif
        }
    }
```

### Keeping Time

Time keeping needs to be handled at least once every 10 seconds. This can be handled two different ways. Both functions require the use of the previously discussed stopwatch variable. The easiest way can be handled in one line seen below.

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.DurationUpdate(__stopwatch.Elapsed);
```

The second way to handle timekeeping can be completed with a more generic function seen below.

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.UpdateStatement(XAPIProperties.Result, ResultOptions.Duration, __stopwatch.Elapsed);
```

One simple way of accomplishing this task is by using an update like shown below.

```csharp
private void Update(){
    if (Time.time > __nextUpdate){
        __nextUpdate += __period;
        Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.DurationUpdate(__stopwatch.Elapsed);
    }
}
```

### Stage Restart Counting

Whenever a stage is restarted a count is kept. This should be tied to the stage restart button in the UI. This can be done using the snippet below.

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.StageRestart();
```

### Adding notes

Adding notes to a simulation adds extra information for later review by the user. **Notes are immutable.** This is accomplished two different ways. The easiest way can be seen in the below snippet.

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.AddResultNote("This is a very useful note");
```

Note adding can also be accomplished by the snippet below.

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.UpdateStatement(XAPIProperties.Result, ResultOptions.Extensions, ResultExtensionOptions.Notes, "This is a very useful note");
```

### Scoring the Simulation

Scoring a simulation has multiple parts. The maximum score, the minimum score, the scaled score, and the raw score. The maximum score is the highest possible score on the simulation and the minimum score is likewise the lowest possible score on the simulation. The raw score on the simulation is the procession of the user and needs to be kept current with progress. **Do not set a scaled score, it is currently automatically set.** The snippet below shows how these can be added to the result of the simulation.

```csharp
//These can be set at the start of the simulation and may already be set when the simulation starts, but most likely not.
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.UpdateStatement(XAPIProperties.Result, ResultOptions.ScoreMax, 100f);
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.UpdateStatement(XAPIProperties.Result, ResultOptions.ScoreMin, 0f);

//This is the user's score that needs to be kept current. 85f is just an example.
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.UpdateStatement(XAPIProperties.Result, ResultOptions.ScoreRaw, 85f);
```

### Simulation pass

If the simulation score is higher than passing this needs to be noted using the below snippet. (ie. if the passing score is 70 and the person has already scored higher than true needs to be passed as the input.)

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.SimulationPassed(true);

//or

Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.UpdateStatement(XAPIProperties.Result, ResultOptions.Success, true);
```

It would be more simple if this were a static variable in the simulation and used as a variable in the bool position. This can also be handled at a different point seen in the ending simulation section.

### Completing the Simulation

If the user completes the simulation it should be noted using the snippet below.

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.SimulationComplete();

//or

Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.UpdateStatement(XAPIProperties.Result, ResultOptions.Completion, true);
```

This can also be handled at a different point seen in the ending simulation section.

### Ending the Simulation

Ending a simulation can be handled a few different ways depending on what has been accomplished. If everything has already been updated then the below snippet can be used to end the simulation.

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.EndSimulation();
```

The below snippet will fill in the needed items that could have been set in completion and success as well as the raw score and duration of the simulation. This is the easiest, most complete way to end a simulation.

> Note: the source shows this line with parameter types included, so it reads as a method signature rather than a call site. It is reproduced as written.

```csharp
Febris.CsharpSimulationLibraryNetStandard.Statement.StatementHandler.EndSimulation(bool success, bool complete, float rawScore, TimeSpan duration);
```