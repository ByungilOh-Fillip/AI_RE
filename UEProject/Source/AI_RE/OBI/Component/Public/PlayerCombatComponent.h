// Copyright MixUpProject. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PlayerCombatComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPrimaryActionHitSignature, AActor*, HitActor);

UCLASS(ClassGroup = (Player), meta = (BlueprintSpawnableComponent))
class AI_RE_API UPlayerCombatComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UPlayerCombatComponent();

	UFUNCTION(BlueprintCallable, Category = "Combat")
	void TryStartPrimaryAction();

	UFUNCTION(BlueprintCallable, Category = "Combat")
	void TryStopPrimaryAction();

	UPROPERTY(BlueprintAssignable, Category = "Combat|Events")
	FOnPrimaryActionHitSignature OnPrimaryActionHit;

	UPROPERTY(EditDefaultsOnly, Category = "Combat")
	float TraceDistance = 300.f;

	UPROPERTY(EditDefaultsOnly, Category = "Combat")
	float BaseDamage = 10.f;

protected:
	virtual void BeginPlay() override;

	void PerformTraceHit();

	bool bIsActionActive = false;

	UPROPERTY()
	FTimerHandle ActionTimerHandle;
};
