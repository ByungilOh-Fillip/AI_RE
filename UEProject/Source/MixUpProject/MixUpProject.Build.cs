// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class MixUpProject : ModuleRules
{
	public MixUpProject(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"UMG",
			"Slate"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });

		PublicIncludePaths.AddRange(new string[] {
			"MixUpProject",
			"MixUpProject/Variant_Combat",
			"MixUpProject/Variant_Combat/AI",
			"MixUpProject/Variant_Combat/Animation",
			"MixUpProject/Variant_Combat/Gameplay",
			"MixUpProject/Variant_Combat/Interfaces",
			"MixUpProject/Variant_Combat/UI",
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
