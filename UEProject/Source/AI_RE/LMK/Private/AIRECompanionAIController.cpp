#include "AIRECompanionAIController.h"

#include "AIRECompanionCharacter.h"

DEFINE_LOG_CATEGORY_STATIC(LogAIRECompanionAIController, Log, All);

AAIRECompanionAIController::AAIRECompanionAIController()
{
	PrimaryActorTick.bCanEverTick = false;
	bAttachToPawn = true;
	bStartAILogicOnPossess = false;
}

void AAIRECompanionAIController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	AAIRECompanionCharacter* PossessedCompanion = Cast<AAIRECompanionCharacter>(InPawn);
	if (!IsValid(PossessedCompanion))
	{
		UE_LOG(LogAIRECompanionAIController, Warning, TEXT("Companion AIController rejected incompatible pawn %s."), *GetNameSafe(InPawn));
		UnPossess();
		return;
	}

	CompanionCharacter = PossessedCompanion;
	StopMovement();
}

void AAIRECompanionAIController::OnUnPossess()
{
	ResetCompanionState();
	Super::OnUnPossess();
}

void AAIRECompanionAIController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	ResetCompanionState();
	Super::EndPlay(EndPlayReason);
}

void AAIRECompanionAIController::ResetCompanionState()
{
	StopMovement();
	CompanionCharacter.Reset();
}
