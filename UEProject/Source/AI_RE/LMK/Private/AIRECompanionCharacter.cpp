#include "AIRECompanionCharacter.h"

#include "AIRECompanionAIController.h"
#include "AIRECompanionConfigDataAsset.h"

DEFINE_LOG_CATEGORY_STATIC(LogAIRECompanionCharacter, Log, All);

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

const UAIRECompanionConfigDataAsset* AAIRECompanionCharacter::GetCompanionConfig() const
{
	if (IsValid(CompanionConfig))
	{
		FText ValidationError;
		if (CompanionConfig->IsConfigurationValid(ValidationError))
		{
			return CompanionConfig;
		}
	}

	return GetDefault<UAIRECompanionConfigDataAsset>();
}

void AAIRECompanionCharacter::BeginPlay()
{
	Super::BeginPlay();

	if (!IsValid(CompanionConfig))
	{
		UE_LOG(LogAIRECompanionCharacter, Warning, TEXT("Companion %s has no configuration assigned. Using C++ defaults."), *GetNameSafe(this));
		return;
	}

	FText ValidationError;
	if (!CompanionConfig->IsConfigurationValid(ValidationError))
	{
		UE_LOG(
			LogAIRECompanionCharacter,
			Warning,
			TEXT("Companion %s has invalid configuration %s: %s Using C++ defaults."),
			*GetNameSafe(this),
			*GetNameSafe(CompanionConfig),
			*ValidationError.ToString());
	}
}
