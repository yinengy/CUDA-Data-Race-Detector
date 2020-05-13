/* 
 *
 * A NVBit tool, which will detect conflict memory access in the kernel.
 * The raw output will be processed by a Pytyhon script
 *
 * Yineng Yan (yinengy@umich.edu), 2020
 */

#include <stdio.h>
#include <unordered_set>

/* header for every nvbit tool */
#include "nvbit_tool.h"

/* interface of nvbit */
#include "nvbit.h"

/* nvbit utility functions */
#include "utils/utils.h"

/* Set used to avoid re-instrumenting the same functions multiple times */
std::unordered_set<CUfunction> already_instrumented;

/* instrument functions, it follows the code of the sample tools in NVbit release */
void instrument_function_if_needed(CUcontext ctx, CUfunction func) {
    /* Get related functions of the kernel (device function that can be
     * called by the kernel) */
    std::vector<CUfunction> related_functions =
        nvbit_get_related_functions(ctx, func);

    /* add kernel itself to the related function vector */
    related_functions.push_back(func);

    /* iterate on function */
    for (auto f : related_functions) {
        /* "recording" function was instrumented, if set insertion failed
         * we have already encountered this function */
        if (!already_instrumented.insert(f).second) {
            continue;
        }

        const std::vector<Instr *> &instrs = nvbit_get_instrs(ctx, f);
        for (auto instr : instrs) {
            // only instrument load & store instructions
            if (instr->getMemOpType()!=Instr::memOpType::GLOBAL
                    && instr->getMemOpType()!=Instr::memOpType::SHARED) {
                continue;
            }

            for (int i = 0; i < instr->getNumOperands(); i++) {
                /* get the operand "i" */
                const Instr::operand_t *op = instr->getOperand(i);

                if (op->type == Instr::operandType::MREF) {
                    /* insert call to the instrumentation function with its
                     * arguments */
                    nvbit_insert_call(instr, "print_ldst", IPOINT_AFTER);
                    /* predicate value */
                    nvbit_add_call_arg_pred_val(instr);
                    /* memory reference 64 bit address */
                    nvbit_add_call_arg_mref_addr64(instr);
                    nvbit_add_call_arg_const_val32(instr, instr->getMemOpType()==Instr::memOpType::SHARED);
                    nvbit_add_call_arg_const_val32(instr, instr->isLoad());
                    break;
                }
            }
        }
    }
}

/* This call-back is triggered every time a CUDA driver call is encountered.
 * Here we can look for a particular CUDA driver call by checking at the
 * call back ids  which are defined in tools_cuda_api_meta.h.
 * This call back is triggered bith at entry and at exit of each CUDA driver
 * call, is_exit=0 is entry, is_exit=1 is exit.
 * */
void nvbit_at_cuda_event(CUcontext ctx, int is_exit, nvbit_api_cuda_t cbid,
                         const char *name, void *params, CUresult *pStatus) {
    /* Identify all the possible CUDA launch events */
    if (cbid == API_CUDA_cuLaunch || cbid == API_CUDA_cuLaunchKernel_ptsz ||
        cbid == API_CUDA_cuLaunchGrid || cbid == API_CUDA_cuLaunchGridAsync ||
        cbid == API_CUDA_cuLaunchKernel) {
        /* cast params to cuLaunch_params since if we are here we know these are
         * the right parameters type */
        cuLaunch_params *p = (cuLaunch_params *)params;

        if (!is_exit) {
            instrument_function_if_needed(ctx, p->f);
            nvbit_enable_instrumented(ctx, p->f, true);
        }
    }
}
