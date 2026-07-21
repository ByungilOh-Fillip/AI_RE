#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AIRECompanionCharacter.generated.h"

class UAIRECompanionConfigDataAsset;

UCLASS(Blueprintable)
class AI_RE_API AAIRECompanionCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AAIRECompanionCharacter();

	UFUNCTION(BlueprintPure, Category = "AIRE|Companion")
	FString GetCompanionId() const;

	UFUNCTION(BlueprintPure, Category = "AIRE|Companion|Configuration")
	const UAIRECompanionConfigDataAsset* GetCompanionConfig() const;

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AIRE|Companion|Configuration", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UAIRECompanionConfigDataAsset> CompanionConfig;
};
