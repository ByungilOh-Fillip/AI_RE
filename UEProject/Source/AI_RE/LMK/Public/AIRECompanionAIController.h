#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "AIRECompanionAIController.generated.h"

class AAIRECompanionCharacter;

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

	TWeakObjectPtr<AAIRECompanionCharacter> CompanionCharacter;
};
