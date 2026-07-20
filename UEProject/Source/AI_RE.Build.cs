// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class AI_RE : ModuleRules
{
	public AI_RE(ReadOnlyTargetRules Target) : base(Target)
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
			"AI_RE/OBI/ThirdPerson",
			"AI_RE/OBI/ThirdPerson/Variant_Combat",
			"AI_RE/OBI/ThirdPerson/Variant_Combat/AI",
			"AI_RE/OBI/ThirdPerson/Variant_Combat/Animation",
			"AI_RE/OBI/ThirdPerson/Variant_Combat/Gameplay",
			"AI_RE/OBI/ThirdPerson/Variant_Combat/Interfaces",
			"AI_RE/OBI/ThirdPerson/Variant_Combat/UI",
			"AI_RE/OBI/Component/Public"
			"AI_RE/Work/LMK/Public",
			
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
