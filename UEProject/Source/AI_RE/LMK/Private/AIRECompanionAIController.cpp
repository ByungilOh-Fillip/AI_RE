#include "AIRECompanionAIController.h"

#include "AIRECompanionCharacter.h"
#include "Components/StateTreeAIComponent.h"

DEFINE_LOG_CATEGORY_STATIC(LogAIRECompanionAIController, Log, All);

AAIRECompanionAIController::AAIRECompanionAIController()
{
	PrimaryActorTick.bCanEverTick = false;
	bAttachToPawn = true;
	bStartAILogicOnPossess = false;

	StateTreeAIComponent = CreateDefaultSubobject<UStateTreeAIComponent>(TEXT("StateTreeAI"));
	check(StateTreeAIComponent);
	StateTreeAIComponent->SetStartLogicAutomatically(false);
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
	StateTreeAIComponent->StartLogic();

	if (!StateTreeAIComponent->IsRunning())
	{
		UE_LOG(
			LogAIRECompanionAIController,
			Warning,
			TEXT("Companion AIController %s could not start its StateTree. Verify the StateTree asset assignment."),
			*GetNameSafe(this));
	}
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
	if (IsValid(StateTreeAIComponent))
	{
		StateTreeAIComponent->StopLogic(TEXT("Companion controller is releasing its pawn."));
	}

	StopMovement();
	CompanionCharacter.Reset();
}
