#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AIRECompanionCharacter.generated.h"

UCLASS(Blueprintable)
class AI_RE_API AAIRECompanionCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AAIRECompanionCharacter();

	UFUNCTION(BlueprintPure, Category = "AIRE|Companion")
	FString GetCompanionId() const;
};
