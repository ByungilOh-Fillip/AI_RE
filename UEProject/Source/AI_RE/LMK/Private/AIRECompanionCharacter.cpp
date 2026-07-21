#include "AIRECompanionCharacter.h"

#include "AIRECompanionAIController.h"

namespace
{
	constexpr TCHAR CompanionId[] = TEXT("MAKO");
}

AAIRECompanionCharacter::AAIRECompanionCharacter()
{
	PrimaryActorTick.bCanEverTick = false;
	AIControllerClass = AAIRECompanionAIController::StaticClass();
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
}

FString AAIRECompanionCharacter::GetCompanionId() const
{
	return CompanionId;
}
