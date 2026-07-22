using UnrealBuildTool;

public class AIREStateTreeMCPToolset : ModuleRules
{
	public AIREStateTreeMCPToolset(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"StateTreeModule",
				"ToolsetRegistry"
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"BlueprintGraph",
				"InputCore",
				"PropertyBindingUtils",
				"StateTreeEditorModule",
				"UnrealEd"
			}
		);
	}
}
