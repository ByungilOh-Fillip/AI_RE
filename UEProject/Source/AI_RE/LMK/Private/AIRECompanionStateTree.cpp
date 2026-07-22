#include "AIRECompanionStateTree.h"

#include "AIRECompanionAIController.h"
#include "AIRECompanionCharacter.h"
#include "AIRECompanionConfigDataAsset.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "StateTreeExecutionContext.h"

DEFINE_LOG_CATEGORY_STATIC(LogAIRECompanionStateTree, Log, All);

namespace
{
	enum class EAIRECompanionBehaviorInput : uint16
	{
		HasPlayer = 1 << 0,
		ShouldFollow = 1 << 1,
		ShouldReturn = 1 << 2,
		Disabled = 1 << 3,
		Survival = 1 << 4,
		Combat = 1 << 5,
		DirectCommand = 1 << 6,
		Work = 1 << 7
	};
	ENUM_CLASS_FLAGS(EAIRECompanionBehaviorInput);

	void AddBehaviorInput(
		EAIRECompanionBehaviorInput& InputMask,
		const EAIRECompanionBehaviorInput Input,
		const bool bIsActive)
	{
		if (bIsActive)
		{
			EnumAddFlags(InputMask, Input);
		}
	}

	FString GetBehaviorStateName(const EAIRECompanionBehaviorState BehaviorState)
	{
		const UEnum* BehaviorStateEnum = StaticEnum<EAIRECompanionBehaviorState>();
		return IsValid(BehaviorStateEnum)
			? BehaviorStateEnum->GetNameStringByValue(static_cast<int64>(BehaviorState))
			: TEXT("Unknown");
	}
}

void FAIRECompanionContextEvaluator::TreeStart(FStateTreeExecutionContext& Context) const
{
	UpdateContext(Context);
}

void FAIRECompanionContextEvaluator::TreeStop(FStateTreeExecutionContext& Context) const
{
	FInstanceDataType& InstanceData = Context.GetInstanceData(*this);
	InstanceData.PlayerPawn = nullptr;
	InstanceData.DistanceToPlayer = 0.0f;
	InstanceData.MovementSpeed = 0.0f;
	InstanceData.FollowStopDistance = 0.0f;
	InstanceData.ReturnStartDistance = 0.0f;
	InstanceData.bHasPlayer = false;
	InstanceData.bShouldFollow = false;
	InstanceData.bShouldReturn = false;
	InstanceData.bIsDisabledRequested = false;
	InstanceData.bIsSurvivalRequested = false;
	InstanceData.bIsCombatRequested = false;
	InstanceData.bIsDirectCommandRequested = false;
	InstanceData.bIsWorkRequested = false;
	InstanceData.bBehaviorSelectionChanged = false;
	InstanceData.PreviousBehaviorInputMask = 0;
	InstanceData.bHasPreviousBehaviorInput = false;
	InstanceData.PreviousPlayerPawn.Reset();
}

void FAIRECompanionContextEvaluator::Tick(FStateTreeExecutionContext& Context, const float) const
{
	UpdateContext(Context);
}

void FAIRECompanionContextEvaluator::UpdateContext(FStateTreeExecutionContext& Context) const
{
	FInstanceDataType& InstanceData = Context.GetInstanceData(*this);
	InstanceData.PlayerPawn = nullptr;
	InstanceData.DistanceToPlayer = 0.0f;
	InstanceData.MovementSpeed = 0.0f;
	InstanceData.FollowStopDistance = 0.0f;
	InstanceData.ReturnStartDistance = 0.0f;
	InstanceData.bHasPlayer = false;
	InstanceData.bShouldFollow = false;
	InstanceData.bShouldReturn = false;
	InstanceData.bIsDisabledRequested = false;
	InstanceData.bIsSurvivalRequested = false;
	InstanceData.bIsCombatRequested = false;
	InstanceData.bIsDirectCommandRequested = false;
	InstanceData.bIsWorkRequested = false;

	if (IsValid(InstanceData.CompanionController))
	{
		InstanceData.bIsDisabledRequested = InstanceData.CompanionController->IsTestBehaviorRequestActive(
			EAIRECompanionTestBehaviorRequest::Disabled);
		InstanceData.bIsSurvivalRequested = InstanceData.CompanionController->IsTestBehaviorRequestActive(
			EAIRECompanionTestBehaviorRequest::Survival);
		InstanceData.bIsCombatRequested = InstanceData.CompanionController->IsTestBehaviorRequestActive(
			EAIRECompanionTestBehaviorRequest::Combat);
		InstanceData.bIsDirectCommandRequested = InstanceData.CompanionController->IsTestBehaviorRequestActive(
			EAIRECompanionTestBehaviorRequest::DirectCommand);
		InstanceData.bIsWorkRequested = InstanceData.CompanionController->IsTestBehaviorRequestActive(
			EAIRECompanionTestBehaviorRequest::Work);
	}

	if (IsValid(InstanceData.CompanionCharacter))
	{
		const UAIRECompanionConfigDataAsset* CompanionConfig = InstanceData.CompanionCharacter->GetCompanionConfig();
		if (IsValid(CompanionConfig))
		{
			InstanceData.MovementSpeed = CompanionConfig->MovementSpeed;
			InstanceData.FollowStopDistance = CompanionConfig->FollowStopDistance;
			InstanceData.ReturnStartDistance = CompanionConfig->ReturnStartDistance;

			const UWorld* World = InstanceData.CompanionCharacter->GetWorld();
			APawn* CurrentPlayerPawn = IsValid(World) ? UGameplayStatics::GetPlayerPawn(World, 0) : nullptr;
			if (IsValid(CurrentPlayerPawn))
			{
				InstanceData.PlayerPawn = CurrentPlayerPawn;
				InstanceData.DistanceToPlayer = FVector::Distance(
					InstanceData.CompanionCharacter->GetActorLocation(),
					CurrentPlayerPawn->GetActorLocation());
				InstanceData.bHasPlayer = true;
				InstanceData.bShouldFollow = InstanceData.DistanceToPlayer > InstanceData.FollowStopDistance;
				InstanceData.bShouldReturn = InstanceData.DistanceToPlayer > InstanceData.ReturnStartDistance;
			}
		}
	}

	EAIRECompanionBehaviorInput BehaviorInputMask = static_cast<EAIRECompanionBehaviorInput>(0);
	AddBehaviorInput(BehaviorInputMask, EAIRECompanionBehaviorInput::HasPlayer, InstanceData.bHasPlayer);
	AddBehaviorInput(BehaviorInputMask, EAIRECompanionBehaviorInput::ShouldFollow, InstanceData.bShouldFollow);
	AddBehaviorInput(BehaviorInputMask, EAIRECompanionBehaviorInput::ShouldReturn, InstanceData.bShouldReturn);
	AddBehaviorInput(BehaviorInputMask, EAIRECompanionBehaviorInput::Disabled, InstanceData.bIsDisabledRequested);
	AddBehaviorInput(BehaviorInputMask, EAIRECompanionBehaviorInput::Survival, InstanceData.bIsSurvivalRequested);
	AddBehaviorInput(BehaviorInputMask, EAIRECompanionBehaviorInput::Combat, InstanceData.bIsCombatRequested);
	AddBehaviorInput(BehaviorInputMask, EAIRECompanionBehaviorInput::DirectCommand, InstanceData.bIsDirectCommandRequested);
	AddBehaviorInput(BehaviorInputMask, EAIRECompanionBehaviorInput::Work, InstanceData.bIsWorkRequested);

	const uint16 CurrentBehaviorInputMask = static_cast<uint16>(BehaviorInputMask);
	const bool bPlayerPawnChanged = InstanceData.PreviousPlayerPawn.Get() != InstanceData.PlayerPawn.Get();
	InstanceData.bBehaviorSelectionChanged = !InstanceData.bHasPreviousBehaviorInput
		|| InstanceData.PreviousBehaviorInputMask != CurrentBehaviorInputMask
		|| bPlayerPawnChanged;
	InstanceData.PreviousBehaviorInputMask = CurrentBehaviorInputMask;
	InstanceData.bHasPreviousBehaviorInput = true;
	InstanceData.PreviousPlayerPawn = InstanceData.PlayerPawn;
}

FAIREApplyCompanionMovementSettingsTask::FAIREApplyCompanionMovementSettingsTask()
{
	bShouldCallTick = false;
	bShouldStateChangeOnReselect = false;
}

EStateTreeRunStatus FAIREApplyCompanionMovementSettingsTask::EnterState(
	FStateTreeExecutionContext& Context,
	const FStateTreeTransitionResult&) const
{
	FInstanceDataType& InstanceData = Context.GetInstanceData(*this);
	if (!IsValid(InstanceData.CompanionCharacter))
	{
		UE_LOG(LogAIRECompanionStateTree, Warning, TEXT("Cannot apply movement settings without a valid Companion Character."));
		return EStateTreeRunStatus::Failed;
	}

	UCharacterMovementComponent* MovementComponent = InstanceData.CompanionCharacter->GetCharacterMovement();
	if (!IsValid(MovementComponent))
	{
		UE_LOG(
			LogAIRECompanionStateTree,
			Warning,
			TEXT("Companion %s has no valid Character Movement Component."),
			*GetNameSafe(InstanceData.CompanionCharacter));
		return EStateTreeRunStatus::Failed;
	}

	if (!FMath::IsFinite(InstanceData.MovementSpeed) || InstanceData.MovementSpeed <= 0.0f)
	{
		UE_LOG(
			LogAIRECompanionStateTree,
			Warning,
			TEXT("Companion %s received invalid movement speed %.2f from its StateTree binding."),
			*GetNameSafe(InstanceData.CompanionCharacter),
			InstanceData.MovementSpeed);
		return EStateTreeRunStatus::Failed;
	}

	MovementComponent->MaxWalkSpeed = InstanceData.MovementSpeed;
	return EStateTreeRunStatus::Succeeded;
}

FAIRECompanionIdleTask::FAIRECompanionIdleTask()
{
	bShouldCallTick = false;
	bShouldStateChangeOnReselect = false;
}

EStateTreeRunStatus FAIRECompanionIdleTask::EnterState(
	FStateTreeExecutionContext&,
	const FStateTreeTransitionResult&) const
{
	return EStateTreeRunStatus::Running;
}

FAIRECompanionBehaviorDebugTask::FAIRECompanionBehaviorDebugTask()
{
	bShouldCallTick = false;
	bShouldStateChangeOnReselect = false;
}

EStateTreeRunStatus FAIRECompanionBehaviorDebugTask::EnterState(
	FStateTreeExecutionContext& Context,
	const FStateTreeTransitionResult& Transition) const
{
	const FInstanceDataType& InstanceData = Context.GetInstanceData(*this);
	UE_LOG(
		LogAIRECompanionStateTree,
		Log,
		TEXT("Companion behavior entered. State=%s Target=%s Priority=%s ChangeType=%s"),
		*GetBehaviorStateName(InstanceData.BehaviorState),
		*GetNameSafe(InstanceData.TargetActor),
		*StaticEnum<EStateTreeTransitionPriority>()->GetNameStringByValue(static_cast<int64>(Transition.Priority)),
		*StaticEnum<EStateTreeStateChangeType>()->GetNameStringByValue(static_cast<int64>(Transition.ChangeType)));
	return EStateTreeRunStatus::Succeeded;
}

void FAIRECompanionBehaviorDebugTask::ExitState(
	FStateTreeExecutionContext& Context,
	const FStateTreeTransitionResult& Transition) const
{
	const FInstanceDataType& InstanceData = Context.GetInstanceData(*this);
	UE_LOG(
		LogAIRECompanionStateTree,
		Log,
		TEXT("Companion behavior exited. State=%s Target=%s RunStatus=%s MoveCancellationBoundary=%s"),
		*GetBehaviorStateName(InstanceData.BehaviorState),
		*GetNameSafe(InstanceData.TargetActor),
		*StaticEnum<EStateTreeRunStatus>()->GetNameStringByValue(static_cast<int64>(Transition.CurrentRunStatus)),
		InstanceData.bOwnsMovementRequest ? TEXT("StateExit") : TEXT("None"));
}
