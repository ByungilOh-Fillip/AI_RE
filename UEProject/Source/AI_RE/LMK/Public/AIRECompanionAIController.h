#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "AIRECompanionAIController.generated.h"

class AAIRECompanionCharacter;
class UStateTreeAIComponent;

UCLASS(Blueprintable)
class AI_RE_API AAIRECompanionAIController : public AAIController
{
	GENERATED_BODY()

public:
	AAIRECompanionAIController();

protected:
	virtual void OnPossess(APawn* InPawn) override;
	virtual void OnUnPossess() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	void ResetCompanionState();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "AIRE|Companion|AI", meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UStateTreeAIComponent> StateTreeAIComponent;

	TWeakObjectPtr<AAIRECompanionCharacter> CompanionCharacter;
};
