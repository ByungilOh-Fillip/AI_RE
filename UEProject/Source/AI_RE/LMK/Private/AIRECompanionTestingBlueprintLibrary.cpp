#include "AIRECompanionTestingBlueprintLibrary.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"

namespace
{
	AAIRECompanionAIController* FindFirstCompanionController(const UObject* WorldContextObject)
	{
		if (!IsValid(GEngine) || !IsValid(WorldContextObject))
		{
			return nullptr;
		}

		UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
		if (!IsValid(World))
		{
			return nullptr;
		}

		for (TActorIterator<AAIRECompanionAIController> Iterator(World); Iterator; ++Iterator)
		{
			if (IsValid(*Iterator))
			{
				return *Iterator;
			}
		}

		return nullptr;
	}
}

bool UAIRECompanionTestingBlueprintLibrary::SetFirstCompanionTestBehaviorRequest(
	const UObject* WorldContextObject,
	const EAIRECompanionTestBehaviorRequest Request,
	const bool bIsRequested)
{
	AAIRECompanionAIController* CompanionController = FindFirstCompanionController(WorldContextObject);
	if (!IsValid(CompanionController))
	{
		return false;
	}

	CompanionController->SetTestBehaviorRequest(Request, bIsRequested);
	return true;
}

bool UAIRECompanionTestingBlueprintLibrary::ClearFirstCompanionTestBehaviorRequests(
	const UObject* WorldContextObject)
{
	AAIRECompanionAIController* CompanionController = FindFirstCompanionController(WorldContextObject);
	if (!IsValid(CompanionController))
	{
		return false;
	}

	CompanionController->ClearTestBehaviorRequests();
	return true;
}
